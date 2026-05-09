# =============================================================================
# 모듈: 라인 히스토리 payload 조립 유틸
# 주요 기능: where/sql 생성, 결과 row 정규화
# 주요 가정: selectors.get_line_history_payload에서 읽기 쿼리 조립에 사용합니다.
# =============================================================================
"""라인 히스토리 집계 payload 조립 유틸리티."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional, Sequence

from ..table_schema import build_date_range_filters

_DRONE_SOP_TABLE = "drone_sop"


def _to_int(value: Any) -> int:
    """값을 정수로 변환하고 실패 시 0을 반환합니다."""

    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0


def normalize_bucket_value(value: Any) -> Optional[str]:
    """날짜/시간 버킷 값을 ISO-like 문자열로 정규화합니다."""

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.replace(minute=0, second=0, microsecond=0).isoformat()

    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time()).isoformat()

    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None

        candidate = cleaned
        if " " in candidate and "T" not in candidate:
            candidate = candidate.replace(" ", "T")

        try:
            parsed = datetime.fromisoformat(candidate)
            return parsed.replace(minute=0, second=0, microsecond=0).isoformat()
        except ValueError:
            return cleaned

    return None


def build_where_clause(
    *,
    timestamp_column: str,
    line_filters: Sequence[str],
    line_params: Sequence[Any],
    from_value: Optional[str],
    to_value: Optional[str],
) -> tuple[str, list[Any]]:
    """라인/날짜 조건을 합쳐 WHERE 절을 구성합니다."""

    conditions = list(line_filters)
    params = list(line_params)

    date_conditions, date_params = build_date_range_filters(timestamp_column, from_value, to_value)
    conditions.extend(date_conditions)
    params.extend(date_params)

    clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return clause, params


def build_totals_query(
    *,
    table_name: str,
    timestamp_column: str,
    send_jira_column: Optional[str],
    where_clause: str,
) -> str:
    """시간 단위 합계 쿼리를 생성합니다."""

    use_delivery_jira_count = table_name == _DRONE_SOP_TABLE and not send_jira_column
    table_expr = f"{table_name} base" if use_delivery_jira_count else table_name
    timestamp_expr = f"base.{timestamp_column}" if use_delivery_jira_count else timestamp_column
    bucket_expr = f"DATE_TRUNC('hour', {timestamp_expr})"
    totals_select = [f"{bucket_expr} AS bucket", "COUNT(*) AS row_count"]
    if send_jira_column:
        totals_select.append(
            "SUM(CASE WHEN {col} > 0 THEN 1 ELSE 0 END) AS send_jira_count".format(col=send_jira_column)
        )
    elif use_delivery_jira_count:
        totals_select.append(
            "SUM(CASE WHEN EXISTS ("
            "SELECT 1 FROM drone_sop_delivery delivery "
            "WHERE delivery.sop_id = base.id "
            "AND delivery.channel = 'jira' "
            "AND delivery.status = 'success'"
            ") THEN 1 ELSE 0 END) AS send_jira_count"
        )
    else:
        totals_select.append("0 AS send_jira_count")

    return """
        SELECT {select_clause}
        FROM {table}
        {where_clause}
        GROUP BY bucket
        ORDER BY bucket ASC
    """.format(
        select_clause=", ".join(totals_select),
        table=table_expr,
        where_clause=where_clause,
    )


def build_breakdown_query(
    *,
    table_name: str,
    timestamp_column: str,
    dimension_column: str,
    send_jira_column: Optional[str],
    where_clause: str,
) -> str:
    """시간 단위 분해(차원별) 쿼리를 생성합니다."""

    use_delivery_jira_count = table_name == _DRONE_SOP_TABLE and not send_jira_column
    table_expr = f"{table_name} base" if use_delivery_jira_count else table_name
    timestamp_expr = f"base.{timestamp_column}" if use_delivery_jira_count else timestamp_column
    dimension_expr = f"base.{dimension_column}" if use_delivery_jira_count else dimension_column
    bucket_expr = f"DATE_TRUNC('hour', {timestamp_expr})"
    select_parts = [
        f"{bucket_expr} AS bucket",
        f"COALESCE(CAST({dimension_expr} AS TEXT), 'Unspecified') AS category",
        "COUNT(*) AS row_count",
    ]

    if send_jira_column:
        select_parts.append(
            "SUM(CASE WHEN {col} > 0 THEN 1 ELSE 0 END) AS send_jira_count".format(col=send_jira_column)
        )
    elif use_delivery_jira_count:
        select_parts.append(
            "SUM(CASE WHEN EXISTS ("
            "SELECT 1 FROM drone_sop_delivery delivery "
            "WHERE delivery.sop_id = base.id "
            "AND delivery.channel = 'jira' "
            "AND delivery.status = 'success'"
            ") THEN 1 ELSE 0 END) AS send_jira_count"
        )
    else:
        select_parts.append("0 AS send_jira_count")

    return """
        SELECT {select_clause}
        FROM {table}
        {where_clause}
        GROUP BY bucket, category
        ORDER BY bucket ASC, category ASC
    """.format(
        select_clause=", ".join(select_parts),
        table=table_expr,
        where_clause=where_clause,
    )


def normalize_daily_row(row: dict[str, Any]) -> dict[str, Any]:
    """합계 row를 응답 형식으로 정규화합니다."""

    date_str = normalize_bucket_value(row.get("bucket") or row.get("day") or row.get("date"))
    return {
        "date": date_str,
        "rowCount": _to_int(row.get("row_count", 0)),
        "sendJiraCount": _to_int(row.get("send_jira_count", 0)),
    }


def normalize_breakdown_row(row: dict[str, Any]) -> dict[str, Any]:
    """분해 row를 응답 형식으로 정규화합니다."""

    date_str = normalize_bucket_value(row.get("bucket") or row.get("day") or row.get("date"))

    category = row.get("category") or row.get("dimension") or "Unspecified"
    if not isinstance(category, str) or not category.strip():
        category = "Unspecified"

    return {
        "date": date_str,
        "category": category.strip() if isinstance(category, str) else str(category),
        "rowCount": _to_int(row.get("row_count", 0)),
        "sendJiraCount": _to_int(row.get("send_jira_count", 0)),
    }


__all__ = [
    "build_breakdown_query",
    "build_totals_query",
    "build_where_clause",
    "normalize_breakdown_row",
    "normalize_daily_row",
]
