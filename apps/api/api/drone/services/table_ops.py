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

from .. import selectors
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


@dataclass(frozen=True)
class UpdateAssignment:
    """검증된 업데이트 컬럼과 정규화된 값을 보관합니다."""

    column_name: str
    value: Any

_ALLOWED_UPDATE_COLUMNS = {"comment", "needtosend", "instant_inform", "status"}
_ALLOWED_TABLES = {table_schema.DEFAULT_TABLE}

_RECENT_HOURS_MIN = 0
_RECENT_HOURS_DAY_STEP = 24
_RECENT_HOURS_DAY_MODE_MIN_DAYS = 2
_RECENT_HOURS_DAY_MODE_MAX_DAYS = 7
_RECENT_HOURS_DAY_MODE_THRESHOLD = 24
_RECENT_HOURS_MAX = _RECENT_HOURS_DAY_MODE_MAX_DAYS * _RECENT_HOURS_DAY_STEP
_RECENT_HOURS_DEFAULT_START = 8
_RECENT_HOURS_DEFAULT_END = 0
_RECENT_FUTURE_TOLERANCE_MINUTES = 5
_DELIVERY_VIRTUAL_COLUMNS = [
    "delivery_targets",
    "delivery_status",
]
_DELIVERY_COLUMN_BY_CHANNEL = {
    "jira": "delivery_jira",
    "messenger": "delivery_messenger",
    "mail": "delivery_mail",
}


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


def _normalize_positive_int(value: Any) -> int | None:
    """양의 정수 ID 값을 정규화합니다."""

    if isinstance(value, int) and value > 0:
        return value
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _summarize_delivery_flag(*, delivery_rows: list[dict[str, Any]], channel: str) -> int:
    """delivery row 목록을 테이블 정렬용 숫자 플래그로 요약합니다."""

    channel_rows = [row for row in delivery_rows if row.get("channel") == channel]
    if not channel_rows:
        return 0
    statuses = {str(row.get("status") or "").strip().lower() for row in channel_rows}
    if "failed" in statuses:
        return -1
    if "pending" in statuses or "unknown" in statuses:
        return 0
    if "success" in statuses:
        return 1
    return 0


def _summarize_delivery_overall_flag(*, delivery_rows: list[dict[str, Any]]) -> int:
    """전체 delivery row 목록을 테이블 정렬용 숫자 플래그로 요약합니다."""

    if not delivery_rows:
        return 0
    statuses = {str(row.get("status") or "").strip().lower() for row in delivery_rows}
    if "failed" in statuses:
        return -1
    if "pending" in statuses or "unknown" in statuses:
        return 0
    if "success" in statuses:
        return 1
    return 0


def _latest_success_sent_at(*, delivery_rows: list[dict[str, Any]]) -> datetime | None:
    """성공 delivery 중 가장 최근 발송 시각을 반환합니다."""

    latest_sent_at: datetime | None = None
    for delivery in delivery_rows:
        if delivery.get("status") != "success":
            continue
        sent_at = delivery.get("sentAt")
        if not isinstance(sent_at, datetime):
            continue
        if latest_sent_at is None or sent_at > latest_sent_at:
            latest_sent_at = sent_at
    return latest_sent_at


def _extract_delivery_targets(delivery_rows: list[dict[str, Any]]) -> list[str]:
    """delivery row에서 중복 없는 target 목록을 추출합니다."""

    targets: list[str] = []
    seen: set[str] = set()
    for delivery in delivery_rows:
        target = delivery.get("targetUserSdwtProd") or delivery.get("target_user_sdwt_prod")
        if not isinstance(target, str) or not target.strip():
            continue
        cleaned = target.strip()
        lookup = cleaned.casefold()
        if lookup in seen:
            continue
        seen.add(lookup)
        targets.append(cleaned)
    return targets


def _attach_delivery_summary_columns(*, row: dict[str, Any], delivery_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """테이블 row에 delivery 가상 컬럼 값을 붙입니다."""

    targets = _extract_delivery_targets(delivery_rows)
    enriched = {
        **row,
        "deliveryRows": delivery_rows,
        "delivery_targets": targets[0] if targets else None,
        "delivery_status": _summarize_delivery_overall_flag(delivery_rows=delivery_rows),
    }
    for channel, column in _DELIVERY_COLUMN_BY_CHANNEL.items():
        enriched[column] = _summarize_delivery_flag(delivery_rows=delivery_rows, channel=channel)

    jira_success = next(
        (
            delivery
            for delivery in delivery_rows
            if delivery.get("channel") == "jira" and delivery.get("status") == "success"
        ),
        None,
    )
    if jira_success:
        enriched["jira_key"] = jira_success.get("externalKey")
        enriched["inform_step"] = jira_success.get("sentStep")
    enriched["informed_at"] = _latest_success_sent_at(delivery_rows=delivery_rows)
    return enriched


def _attach_delivery_rows(*, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """테이블 row에 target/channel delivery 메타를 붙입니다."""

    if not rows:
        return rows

    sop_ids = [
        sop_id
        for row in rows
        if isinstance(row, dict) and (sop_id := _normalize_positive_int(row.get("id"))) is not None
    ]
    delivery_rows_by_sop_id = selectors.list_drone_sop_channel_delivery_rows_by_sop_ids(sop_ids=sop_ids)
    enriched_rows: list[dict[str, Any]] = []
    for row in rows:
        sop_id = _normalize_positive_int(row.get("id")) if isinstance(row, dict) else None
        delivery_rows = delivery_rows_by_sop_id.get(sop_id or 0, [])
        enriched_rows.append(_attach_delivery_summary_columns(row=row, delivery_rows=delivery_rows))
    return enriched_rows


def _append_delivery_columns(column_names: list[str]) -> list[str]:
    """DB 컬럼 목록에 delivery 가상 컬럼을 추가합니다."""

    response_columns = list(column_names)
    for summary_column in ("informed_at", "jira_key"):
        if summary_column not in response_columns:
            response_columns.append(summary_column)
    insert_index = len(response_columns)
    for anchor in ("sdwt_prod", "user_sdwt_prod", "line_id"):
        if anchor in response_columns:
            insert_index = response_columns.index(anchor) + 1
            break
    for column in reversed(_DELIVERY_VIRTUAL_COLUMNS):
        if column in response_columns:
            continue
        response_columns.insert(insert_index, column)
    return response_columns


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


def _normalize_update_items(*, updates: Mapping[str, Any]) -> list[tuple[str, Any]]:
    """허용된 컬럼과 null이 아닌 값만 업데이트 후보로 남깁니다."""

    return [
        (key, value)
        for key, value in updates.items()
        if key in _ALLOWED_UPDATE_COLUMNS and value is not None
    ]


def _build_update_assignments(
    *,
    column_names: Sequence[str],
    update_items: Sequence[tuple[str, Any]],
) -> list[UpdateAssignment]:
    """실제 DB 컬럼이 존재하는 업데이트 항목만 SQL assignment로 변환합니다."""

    assignments: list[UpdateAssignment] = []
    for key, value in update_items:
        column_name = table_schema.find_column(column_names, key)
        if not column_name:
            continue
        assignments.append(
            UpdateAssignment(
                column_name=column_name,
                value=_normalize_update_value(key, value),
            )
        )
    return assignments


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
