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
from .table_delivery import (
    append_delivery_columns as _append_delivery_columns,
    attach_delivery_rows as _attach_delivery_rows,
)
from .table_normalization import (
    build_update_assignments as _build_update_assignments,
    normalize_update_items as _normalize_update_items,
    resolve_recent_hours_range as _resolve_recent_hours_range,
)


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


_ALLOWED_TABLES = {table_schema.DEFAULT_TABLE}

_RECENT_FUTURE_TOLERANCE_MINUTES = 5


def _raise_if_table_missing(exc: Exception, table_name: str) -> None:
    """테이블 누락 오류를 감지해 TableNotFoundError로 변환합니다."""

    error_code = getattr(exc, "code", None) or getattr(exc, "pgcode", None)
    if error_code in {"ER_NO_SUCH_TABLE", "42P01"}:
        raise TableNotFoundError(table_name=table_name) from exc


def _resolve_allowed_table_name(value: Any) -> str:
    """지원하는 Drone SOP 테이블명만 정규화해서 반환합니다."""

    table_name = table_schema.sanitize_identifier(value, table_schema.DEFAULT_TABLE)
    if not table_name or table_name not in _ALLOWED_TABLES:
        raise ValueError("Only drone_sop table is supported")
    return table_name


def _resolve_id_column(*, table_name: str, column_names: Sequence[str]) -> str:
    """업데이트 대상 테이블의 id 컬럼을 확인합니다."""

    id_column = table_schema.find_column(column_names, "id")
    if not id_column:
        raise ValueError(f'Table "{table_name}" does not expose an id column')
    return id_column


def _fetch_rows(*, sql: str, params: Sequence[Any]) -> list[dict[str, Any]]:
    """SQL 조회 결과를 row 목록으로 반환합니다."""

    return run_query(sql, list(params))


def _fetch_row(*, sql: str, params: Sequence[Any]) -> dict[str, Any] | None:
    """SQL 조회 결과 중 첫 번째 row를 반환합니다."""

    rows = _fetch_rows(sql=sql, params=params)
    return rows[0] if rows else None


def _fetch_table_record(*, table_name: str, id_column: str, record_id: Any) -> dict[str, Any] | None:
    """테이블명/id 컬럼 검증 이후 단일 record를 조회합니다."""

    return _fetch_row(
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


def get_table_list_payload(*, params: Mapping[str, Any]) -> dict[str, Any]:
    """테이블 조회 결과를 응답 payload로 구성합니다."""

    from_param = table_schema.normalize_date_only(params.get("from"))
    to_param = table_schema.normalize_date_only(params.get("to"))
    normalized_line_id = table_schema.normalize_line_id(params.get("lineId"))
    line_filter_mode = table_schema.normalize_line_filter_mode(
        params.get("lineFilterMode"),
        default=table_schema.LINE_FILTER_MODE_TARGET_USER_SDWT,
    )
    recent_hours_start, recent_hours_end = _resolve_recent_hours_range(params)

    if from_param and to_param:
        from_param, to_param = table_schema.ensure_date_bounds(from_param, to_param)

    table_name = _resolve_allowed_table_name(params.get("table"))
    schema = table_schema.resolve_table_schema(
        table_name,
        default_table=table_schema.DEFAULT_TABLE,
        require_timestamp=True,
    )
    table_name = schema.name
    column_names = schema.columns
    base_ts_col = schema.timestamp_column
    assert base_ts_col is not None

    line_filter_result = table_schema.build_line_filters(
        column_names,
        normalized_line_id,
        filter_mode=line_filter_mode,
    )
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

    rows = _attach_delivery_rows(rows=rows)
    response_columns = _append_delivery_columns(column_names)

    return {
        "table": table_name,
        "cutoff": (
            "{col} BETWEEN NOW() - INTERVAL '{start} hours' AND NOW() - INTERVAL '{end} hours'"
        ).format(col=base_ts_col, start=recent_hours_start, end=recent_hours_end),
        "from": from_param or None,
        "to": to_param or None,
        "rowCount": len(rows),
        "columns": response_columns,
        "rows": rows,
    }


def update_table_record(*, payload: Mapping[str, Any]) -> TableUpdateResult:
    """테이블 레코드를 부분 업데이트합니다."""

    table_name = _resolve_allowed_table_name(payload.get("table"))

    record_id = payload.get("id")
    if record_id in (None, ""):
        raise ValueError("Record id is required")

    updates = payload.get("updates")
    if not isinstance(updates, dict):
        raise ValueError("Updates must be an object")

    update_items = _normalize_update_items(updates=updates)
    if not update_items:
        raise ValueError("No valid updates provided")

    try:
        column_names = table_schema.list_table_columns(table_name)
    except Exception as exc:  # 방어적 처리: pragma: no cover
        _raise_if_table_missing(exc, table_name)
        raise

    id_column = _resolve_id_column(table_name=table_name, column_names=column_names)
    previous_row = _fetch_table_record(table_name=table_name, id_column=id_column, record_id=record_id)

    assignments = _build_update_assignments(column_names=column_names, update_items=update_items)
    if not assignments:
        raise ValueError("No matching columns to update")

    assignment_sql = [f"{assignment.column_name} = %s" for assignment in assignments]
    query_params = [assignment.value for assignment in assignments]
    query_params.append(record_id)
    sql = (
        """
        UPDATE {table}
        SET {assignments}
        WHERE {id_column} = %s
        """
    ).format(table=table_name, assignments=", ".join(assignment_sql), id_column=id_column)

    try:
        affected, _ = execute(sql, query_params)
    except Exception as exc:  # 방어적 처리: pragma: no cover
        _raise_if_table_missing(exc, table_name)
        raise

    if affected == 0:
        raise TableRecordNotFoundError("Record not found")

    updated_row = _fetch_table_record(table_name=table_name, id_column=id_column, record_id=record_id)

    return TableUpdateResult(
        table_name=table_name,
        previous_row=previous_row,
        updated_row=updated_row,
    )


__all__ = [
    "TableNotFoundError",
    "TableRecordNotFoundError",
    "TableUpdateResult",
    "get_table_list_payload",
    "update_table_record",
]
