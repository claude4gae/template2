# =============================================================================
# 모듈: Drone 테이블 조회/업데이트 서비스
# 주요 기능: /api/v1/line-dashboard/tables 계열 조회/수정 로직 제공
# 주요 가정: line-dashboard 도메인에서 테이블 조회/수정 책임을 단일 관리합니다.
# =============================================================================
"""Drone 도메인 기준 테이블 조회/업데이트 서비스 모듈."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Mapping, Sequence

from api.common.services.db import execute, run_query

from . import table_schema


class TableNotFoundError(LookupError):
    """요청한 테이블이 존재하지 않을 때 발생합니다."""

    def __init__(self, table_name: str) -> None:
        super().__init__(f'Table "{table_name}" was not found')
        self.table_name = table_name


class TableRecordNotFoundError(LookupError):
    """요청한 레코드가 없을 때 발생합니다."""


@dataclass(frozen=True)
class TableUpdateResult:
    """테이블 업데이트 결과."""

    table_name: str
    previous_row: dict[str, Any] | None
    updated_row: dict[str, Any] | None

_ALLOWED_UPDATE_COLUMNS = {"comment", "needtosend", "instant_inform", "status"}

_RECENT_HOURS_MIN = 0
_RECENT_HOURS_DAY_STEP = 24
_RECENT_HOURS_DAY_MODE_MIN_DAYS = 2
_RECENT_HOURS_DAY_MODE_MAX_DAYS = 7
_RECENT_HOURS_DAY_MODE_THRESHOLD = 24
_RECENT_HOURS_MAX = _RECENT_HOURS_DAY_MODE_MAX_DAYS * _RECENT_HOURS_DAY_STEP
_RECENT_HOURS_DEFAULT_START = 8
_RECENT_HOURS_DEFAULT_END = 0
_RECENT_FUTURE_TOLERANCE_MINUTES = 5


def _raise_if_table_missing(exc: Exception, table_name: str) -> None:
    """테이블 누락 오류를 감지해 TableNotFoundError로 변환합니다."""

    error_code = getattr(exc, "code", None) or getattr(exc, "pgcode", None)
    if error_code in {"ER_NO_SUCH_TABLE", "42P01"}:
        raise TableNotFoundError(table_name=table_name) from exc


def _fetch_rows(*, sql: str, params: Sequence[Any]) -> list[dict[str, Any]]:
    """SQL 조회 결과를 row 목록으로 반환합니다."""

    return run_query(sql, list(params))


def _fetch_row(*, sql: str, params: Sequence[Any]) -> dict[str, Any] | None:
    """SQL 조회 결과 중 첫 번째 row를 반환합니다."""

    rows = _fetch_rows(sql=sql, params=params)
    return rows[0] if rows else None


def _snap_recent_hours(value: int) -> int:
    """recentHours 값을 허용 범위/일 단위 규칙으로 보정합니다."""

    clamped = max(_RECENT_HOURS_MIN, min(value, _RECENT_HOURS_MAX))
    if clamped <= _RECENT_HOURS_DAY_MODE_THRESHOLD:
        return clamped

    days = (clamped + _RECENT_HOURS_DAY_STEP - 1) // _RECENT_HOURS_DAY_STEP
    bounded_days = max(
        _RECENT_HOURS_DAY_MODE_MIN_DAYS,
        min(days, _RECENT_HOURS_DAY_MODE_MAX_DAYS),
    )
    return bounded_days * _RECENT_HOURS_DAY_STEP


def _clamp_recent_hours(value: Any, fallback: int) -> int:
    """입력값을 recentHours 규칙에 맞게 정수 보정합니다."""

    try:
        numeric = int(value)
    except (TypeError, ValueError):
        numeric = fallback
    return _snap_recent_hours(numeric)


def _resolve_recent_hours_range(params: Mapping[str, Any]) -> tuple[int, int]:
    """recentHoursStart/End를 해석하고 역전 값을 보정합니다."""

    start = _clamp_recent_hours(params.get("recentHoursStart"), _RECENT_HOURS_DEFAULT_START)
    end = _clamp_recent_hours(params.get("recentHoursEnd"), _RECENT_HOURS_DEFAULT_END)
    if start < end:
        start = end
    return start, end


def get_table_list_payload(*, params: Mapping[str, Any]) -> dict[str, Any]:
    """테이블 조회 결과를 응답 payload로 구성합니다."""

    from_param = table_schema.normalize_date_only(params.get("from"))
    to_param = table_schema.normalize_date_only(params.get("to"))
    normalized_line_id = table_schema.normalize_line_id(params.get("lineId"))
    recent_hours_start, recent_hours_end = _resolve_recent_hours_range(params)

    if from_param and to_param:
        from_param, to_param = table_schema.ensure_date_bounds(from_param, to_param)

    schema = table_schema.resolve_table_schema(
        params.get("table"),
        default_table=table_schema.DEFAULT_TABLE,
        require_timestamp=True,
    )
    table_name = schema.name
    column_names = schema.columns
    base_ts_col = schema.timestamp_column
    assert base_ts_col is not None

    line_filter_result = table_schema.build_line_filters(column_names, normalized_line_id)
    where_parts = list(line_filter_result["filters"])
    query_params = list(line_filter_result["params"])

    now_utc = datetime.utcnow()
    recent_start_dt = now_utc - timedelta(hours=recent_hours_start)
    recent_end_dt = now_utc - timedelta(hours=recent_hours_end)
    recent_end_dt += timedelta(minutes=_RECENT_FUTURE_TOLERANCE_MINUTES)

    where_parts.append(f"{base_ts_col} BETWEEN %s AND %s")
    query_params.append(recent_start_dt.strftime("%Y-%m-%d %H:%M:%S"))
    query_params.append(recent_end_dt.strftime("%Y-%m-%d %H:%M:%S"))

    date_conditions, date_params = table_schema.build_date_range_filters(base_ts_col, from_param, to_param)
    where_parts.extend(date_conditions)
    query_params.extend(date_params)

    where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
    order_clause = f"ORDER BY {base_ts_col} DESC, id DESC"

    try:
        rows = _fetch_rows(
            sql=(
                """
                SELECT *
                FROM {table}
                {where_clause}
                {order_clause}
                """
            ).format(table=table_name, where_clause=where_clause, order_clause=order_clause),
            params=query_params,
        )
    except Exception as exc:  # 방어적 처리(커버리지 제외): pragma: no cover
        _raise_if_table_missing(exc, table_name)
        raise

    return {
        "table": table_name,
        "cutoff": (
            "{col} BETWEEN NOW() - INTERVAL '{start} hours' AND NOW() - INTERVAL '{end} hours'"
        ).format(col=base_ts_col, start=recent_hours_start, end=recent_hours_end),
        "from": from_param or None,
        "to": to_param or None,
        "rowCount": len(rows),
        "columns": column_names,
        "rows": rows,
    }


def update_table_record(*, payload: Mapping[str, Any]) -> TableUpdateResult:
    """테이블 레코드를 부분 업데이트합니다."""

    table_name = table_schema.sanitize_identifier(payload.get("table"), table_schema.DEFAULT_TABLE)
    if not table_name:
        raise ValueError("Invalid table name")

    record_id = payload.get("id")
    if record_id in (None, ""):
        raise ValueError("Record id is required")

    updates = payload.get("updates")
    if not isinstance(updates, dict):
        raise ValueError("Updates must be an object")

    filtered = [
        (key, value)
        for key, value in updates.items()
        if key in _ALLOWED_UPDATE_COLUMNS and value is not None
    ]
    if not filtered:
        raise ValueError("No valid updates provided")

    try:
        column_names = table_schema.list_table_columns(table_name)
    except Exception as exc:  # 방어적 처리: pragma: no cover
        _raise_if_table_missing(exc, table_name)
        raise

    id_column = table_schema.find_column(column_names, "id")
    if not id_column:
        raise ValueError(f'Table "{table_name}" does not expose an id column')

    previous_row = _fetch_row(
        sql=(
            """
            SELECT *
            FROM {table}
            WHERE {id_column} = %s
            LIMIT 1
            """
        ).format(table=table_name, id_column=id_column),
        params=[record_id],
    )

    assignments: list[str] = []
    query_params: list[Any] = []
    for key, value in filtered:
        column_name = table_schema.find_column(column_names, key)
        if not column_name:
            continue
        assignments.append(f"{column_name} = %s")
        query_params.append(_normalize_update_value(key, value))

    if not assignments:
        raise ValueError("No matching columns to update")

    query_params.append(record_id)
    sql = (
        """
        UPDATE {table}
        SET {assignments}
        WHERE {id_column} = %s
        """
    ).format(table=table_name, assignments=", ".join(assignments), id_column=id_column)

    try:
        affected, _ = execute(sql, query_params)
    except Exception as exc:  # 방어적 처리: pragma: no cover
        _raise_if_table_missing(exc, table_name)
        raise

    if affected == 0:
        raise TableRecordNotFoundError("Record not found")

    updated_row = _fetch_row(
        sql=(
            """
            SELECT *
            FROM {table}
            WHERE {id_column} = %s
            LIMIT 1
            """
        ).format(table=table_name, id_column=id_column),
        params=[record_id],
    )

    return TableUpdateResult(
        table_name=table_name,
        previous_row=previous_row,
        updated_row=updated_row,
    )


def _normalize_update_value(key: str, value: Any) -> Any:
    """컬럼별 업데이트 값을 정규화합니다."""

    if key == "comment":
        return "" if value is None else str(value)
    if key == "needtosend":
        return _coerce_smallint_flag(value)
    if key == "instant_inform":
        return _coerce_smallint_flag(value)
    if key == "status":
        return "" if value is None else str(value)
    return value


def _coerce_smallint_flag(value: Any) -> int:
    """다양한 입력을 0~127 범위 정수로 변환합니다."""

    tiny_min, tiny_max = 0, 127

    def clamp(numeric: int) -> int:
        return max(tiny_min, min(tiny_max, int(numeric)))

    if isinstance(value, bool):
        return 1 if value else 0
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return clamp(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "t", "y", "yes"}:
            return 1
        if normalized in {"0", "false", "f", "n", "no", ""}:
            return 0
        try:
            parsed = int(float(normalized))
            return clamp(parsed)
        except (TypeError, ValueError):
            return 0
    try:
        coerced = int(value)
        return clamp(coerced)
    except (TypeError, ValueError):
        return 0


__all__ = [
    "TableNotFoundError",
    "TableRecordNotFoundError",
    "TableUpdateResult",
    "get_table_list_payload",
    "update_table_record",
]
