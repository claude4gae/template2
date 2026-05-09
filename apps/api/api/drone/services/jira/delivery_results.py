"""Drone SOP Jira delivery 결과 계산 helper."""

from __future__ import annotations

from typing import Any, Sequence

from ..shared.delivery_state import normalize_positive_ids


def collect_attempted_delivery_ids(*, rows: Sequence[dict[str, Any]]) -> list[int]:
    """Jira 전송을 시도한 delivery ID 목록을 정규화합니다."""

    return normalize_delivery_ids(
        [int(row["delivery_id"]) for row in rows if isinstance(row.get("delivery_id"), int)]
    )


def normalize_delivery_ids(values: Sequence[int]) -> list[int]:
    """delivery ID 목록을 양의 정수 기준으로 정규화합니다."""

    return normalize_positive_ids(values)


def collect_failed_delivery_ids(*, attempted_ids: Sequence[int], done_ids: Sequence[int]) -> list[int]:
    """시도한 delivery 중 성공하지 못한 ID 목록을 반환합니다."""

    normalized_done_ids = set(normalize_delivery_ids(done_ids))
    return [
        delivery_id
        for delivery_id in normalize_delivery_ids(attempted_ids)
        if delivery_id not in normalized_done_ids
    ]


def count_updated_sop_rows(
    *,
    done_delivery_ids: Sequence[int],
    sop_id_by_delivery_id: dict[int, int],
) -> int:
    """성공 delivery ID 기준으로 업데이트된 SOP row 수를 계산합니다."""

    return len(
        {
            sop_id_by_delivery_id[delivery_id]
            for delivery_id in normalize_delivery_ids(done_delivery_ids)
            if delivery_id in sop_id_by_delivery_id
        }
    )


__all__ = [
    "collect_attempted_delivery_ids",
    "collect_failed_delivery_ids",
    "count_updated_sop_rows",
    "normalize_delivery_ids",
]
