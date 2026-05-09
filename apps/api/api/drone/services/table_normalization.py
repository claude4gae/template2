"""Drone 테이블 조회/수정 입력 정규화 helper 모음."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from . import table_schema


@dataclass(frozen=True)
class UpdateAssignment:
    """검증된 업데이트 컬럼과 정규화된 값을 보관합니다."""

    column_name: str
    value: Any


_ALLOWED_UPDATE_COLUMNS = {"comment", "needtosend", "instant_inform", "status"}

_RECENT_HOURS_MIN = 0
_RECENT_HOURS_DAY_STEP = 24
_RECENT_HOURS_DAY_MODE_MIN_DAYS = 2
_RECENT_HOURS_DAY_MODE_MAX_DAYS = 7
_RECENT_HOURS_DAY_MODE_THRESHOLD = 24
_RECENT_HOURS_MAX = _RECENT_HOURS_DAY_MODE_MAX_DAYS * _RECENT_HOURS_DAY_STEP
_RECENT_HOURS_DEFAULT_START = 8
_RECENT_HOURS_DEFAULT_END = 0


def snap_recent_hours(value: int) -> int:
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


def clamp_recent_hours(value: Any, fallback: int) -> int:
    """입력값을 recentHours 규칙에 맞게 정수 보정합니다."""

    try:
        numeric = int(value)
    except (TypeError, ValueError):
        numeric = fallback
    return snap_recent_hours(numeric)


def resolve_recent_hours_range(params: Mapping[str, Any]) -> tuple[int, int]:
    """recentHoursStart/End를 해석하고 역전 값을 보정합니다."""

    start = clamp_recent_hours(params.get("recentHoursStart"), _RECENT_HOURS_DEFAULT_START)
    end = clamp_recent_hours(params.get("recentHoursEnd"), _RECENT_HOURS_DEFAULT_END)
    if start < end:
        start = end
    return start, end


def normalize_update_items(*, updates: Mapping[str, Any]) -> list[tuple[str, Any]]:
    """허용된 컬럼과 null이 아닌 값만 업데이트 후보로 남깁니다."""

    return [
        (key, value)
        for key, value in updates.items()
        if key in _ALLOWED_UPDATE_COLUMNS and value is not None
    ]


def build_update_assignments(
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
                value=normalize_update_value(key, value),
            )
        )
    return assignments


def normalize_update_value(key: str, value: Any) -> Any:
    """컬럼별 업데이트 값을 정규화합니다."""

    if key == "comment":
        return "" if value is None else str(value)
    if key == "needtosend":
        return coerce_smallint_flag(value)
    if key == "instant_inform":
        return coerce_smallint_flag(value)
    if key == "status":
        return "" if value is None else str(value)
    return value


def coerce_smallint_flag(value: Any) -> int:
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
    "UpdateAssignment",
    "build_update_assignments",
    "normalize_update_items",
    "resolve_recent_hours_range",
]
