"""Drone 테이블 날짜/라인 필터 helper."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional, Sequence

LINE_SDWT_TABLE_NAME = "account_affiliation"
LINE_FILTER_MODE_LEGACY = "legacy"
LINE_FILTER_MODE_SDWT = "sdwt_prod"
LINE_FILTER_MODE_USER_SDWT = "user_sdwt_prod"
LINE_FILTER_MODE_TARGET_USER_SDWT = "target_user_sdwt_prod"
DATE_ONLY_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def normalize_date_only(value: Any) -> Optional[str]:
    """YYYY-MM-DD 형식 문자열만 허용합니다."""

    if not isinstance(value, str):
        return None
    candidate = value.strip()
    return candidate if DATE_ONLY_REGEX.match(candidate) else None


def normalize_line_id(value: Any) -> Optional[str]:
    """lineId 파라미터를 정규화합니다."""

    if not isinstance(value, str):
        return None
    trimmed = value.strip()
    return trimmed or None


def normalize_line_filter_mode(
    value: Any,
    *,
    default: str = LINE_FILTER_MODE_TARGET_USER_SDWT,
) -> str:
    """lineFilterMode 파라미터를 정규화합니다."""

    if not isinstance(value, str):
        return default
    normalized = value.strip().lower()
    if normalized in {
        LINE_FILTER_MODE_LEGACY,
        LINE_FILTER_MODE_SDWT,
        LINE_FILTER_MODE_USER_SDWT,
        LINE_FILTER_MODE_TARGET_USER_SDWT,
    }:
        return normalized
    return default


def ensure_date_bounds(from_value: Optional[str], to_value: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """날짜 범위가 역전되었으면 자동으로 교정합니다."""

    if from_value and to_value:
        try:
            from_time = datetime.fromisoformat(f"{from_value}T00:00:00")
            to_time = datetime.fromisoformat(f"{to_value}T00:00:00")
        except ValueError:
            return from_value, to_value
        if from_time > to_time:
            return to_value, from_value
    return from_value, to_value


def find_column(column_names: Sequence[str], target: str) -> Optional[str]:
    """컬럼 목록에서 대소문자 무시 일치 항목을 찾습니다."""

    target_lower = target.lower()
    for name in column_names:
        if isinstance(name, str) and name.lower() == target_lower:
            return name
    return None


def _build_line_sdwt_subquery_filter(*, column_name: str) -> str:
    """account_affiliation(line, user_sdwt_prod) 서브쿼리 기반 필터를 생성합니다."""

    return (
        "LOWER({col}) IN ("
        "SELECT LOWER(user_sdwt_prod) FROM {table} "
        "WHERE line = %s "
        "AND user_sdwt_prod IS NOT NULL "
        "AND user_sdwt_prod <> ''"
        ")".format(col=column_name, table=LINE_SDWT_TABLE_NAME)
    )


def build_line_filters(
    column_names: Sequence[str],
    line_id: Optional[str],
    *,
    filter_mode: str = LINE_FILTER_MODE_LEGACY,
) -> dict[str, Any]:
    """lineId 기반 필터 SQL 조각을 생성합니다."""

    filters: list[str] = []
    params: list[Any] = []

    if not line_id:
        return {"filters": filters, "params": params}

    normalized_mode = normalize_line_filter_mode(
        filter_mode,
        default=LINE_FILTER_MODE_LEGACY,
    )

    if normalized_mode == LINE_FILTER_MODE_TARGET_USER_SDWT:
        target_col = find_column(column_names, "target_user_sdwt_prod")
        if target_col:
            filters.append(_build_line_sdwt_subquery_filter(column_name=target_col))
            params.append(line_id)
            return {"filters": filters, "params": params}

        user_sdwt_col = find_column(column_names, "user_sdwt_prod")
        if user_sdwt_col:
            filters.append(_build_line_sdwt_subquery_filter(column_name=user_sdwt_col))
            params.append(line_id)
            return {"filters": filters, "params": params}

    if normalized_mode == LINE_FILTER_MODE_USER_SDWT:
        user_sdwt_col = find_column(column_names, "user_sdwt_prod")
        if user_sdwt_col:
            filters.append(_build_line_sdwt_subquery_filter(column_name=user_sdwt_col))
            params.append(line_id)
            return {"filters": filters, "params": params}

        target_col = find_column(column_names, "target_user_sdwt_prod")
        if target_col:
            filters.append(_build_line_sdwt_subquery_filter(column_name=target_col))
            params.append(line_id)
            return {"filters": filters, "params": params}

    if normalized_mode == LINE_FILTER_MODE_SDWT:
        sdwt_col = find_column(column_names, "sdwt_prod")
        if sdwt_col:
            filters.append(_build_line_sdwt_subquery_filter(column_name=sdwt_col))
            params.append(line_id)
            return {"filters": filters, "params": params}

    if normalized_mode == LINE_FILTER_MODE_LEGACY:
        sdwt_col = find_column(column_names, "sdwt_prod")
        if sdwt_col:
            filters.append(_build_line_sdwt_subquery_filter(column_name=sdwt_col))
            params.append(line_id)
            return {"filters": filters, "params": params}

        user_sdwt_col = find_column(column_names, "user_sdwt_prod")
        if user_sdwt_col:
            filters.append(_build_line_sdwt_subquery_filter(column_name=user_sdwt_col))
            params.append(line_id)
            return {"filters": filters, "params": params}

    line_col = find_column(column_names, "line_id")
    if line_col:
        filters.append(f"{line_col} = %s")
        params.append(line_id)

    return {"filters": filters, "params": params}


def build_date_range_filters(
    timestamp_column: str,
    from_value: Optional[str],
    to_value: Optional[str],
) -> tuple[list[str], list[Any]]:
    """날짜 범위 필터 SQL 조각과 파라미터를 구성합니다."""

    filters: list[str] = []
    params: list[Any] = []

    if from_value:
        filters.append(f"{timestamp_column} >= %s")
        params.append(f"{from_value} 00:00:00")
    if to_value:
        filters.append(f"{timestamp_column} <= %s")
        params.append(f"{to_value} 23:59:59")

    return filters, params


__all__ = [
    "LINE_FILTER_MODE_LEGACY",
    "LINE_FILTER_MODE_SDWT",
    "LINE_FILTER_MODE_TARGET_USER_SDWT",
    "LINE_FILTER_MODE_USER_SDWT",
    "LINE_SDWT_TABLE_NAME",
    "build_date_range_filters",
    "build_line_filters",
    "ensure_date_bounds",
    "find_column",
    "normalize_date_only",
    "normalize_line_filter_mode",
    "normalize_line_id",
]
