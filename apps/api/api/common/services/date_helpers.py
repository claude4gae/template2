# common/services/date_helpers.py
"""날짜 및 시간 관련 헬퍼 함수 모음."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple


def ensure_date_bounds(from_value: Optional[str], to_value: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """from/to 날짜 범위가 뒤집힌 경우 순서를 교정합니다."""
    if from_value and to_value:
        try:
            from_time = datetime.fromisoformat(f"{from_value}T00:00:00")
            to_time = datetime.fromisoformat(f"{to_value}T00:00:00")
        except ValueError:
            return from_value, to_value
        if from_time > to_time:
            return to_value, from_value
    return from_value, to_value


def build_date_range_filters(
    timestamp_column: str, from_value: Optional[str], to_value: Optional[str]
) -> Tuple[List[str], List[str]]:
    """타임스탬프 컬럼 기준의 WHERE 조건과 파라미터를 생성합니다."""
    conditions: List[str] = []
    params: List[str] = []

    if from_value:
        conditions.append(f"{timestamp_column} >= %s")
        params.append(f"{from_value} 00:00:00")

    if to_value:
        conditions.append(f"{timestamp_column} <= %s")
        params.append(f"{to_value} 23:59:59")

    return conditions, params

__all__ = ["ensure_date_bounds", "build_date_range_filters"]
