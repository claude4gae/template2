"""Drone SOP inform 상태 처리 helper."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, Sequence

from ...models import DroneSopChannelDelivery
from ..shared.delivery_state import mark_channel_delivery_status, normalize_positive_ids
from .delivery_preparation import extract_row_id

logger = logging.getLogger(__name__)


def filter_rows_by_excluded_ids(*, rows: list[dict[str, Any]], excluded_ids: Sequence[int]) -> list[dict[str, Any]]:
    """제외할 SOP ID를 기준으로 row 목록을 필터링합니다."""

    excluded_set = set(normalize_positive_ids(excluded_ids))
    if not excluded_set:
        return rows
    return [
        row
        for row in rows
        if (row_id := extract_row_id(row)) is not None and row_id not in excluded_set
    ]


def mark_delivery_failed(*, delivery_id: int, reason: str) -> None:
    """단일 delivery 실패 상태 기록을 한 곳에서 수행합니다."""

    mark_channel_delivery_status(
        delivery_ids=[delivery_id],
        status=DroneSopChannelDelivery.Statuses.FAILED,
        reason=reason,
    )


def mark_successful_deliveries(*, delivery_ids: Sequence[int]) -> None:
    """성공 delivery ID 목록을 한 번에 성공 상태로 기록합니다."""

    mark_channel_delivery_status(
        delivery_ids=delivery_ids,
        status=DroneSopChannelDelivery.Statuses.SUCCESS,
    )


def run_count_channel_safely(*, channel_label: str, runner: Callable[[], int]) -> int:
    """채널별 예외를 격리하고 실패 시 0건 처리로 이어갑니다."""

    try:
        return int(runner() or 0)
    except Exception:
        logger.exception("Drone SOP %s pipeline failed during pipeline run", channel_label)
        return 0


__all__ = [
    "filter_rows_by_excluded_ids",
    "mark_delivery_failed",
    "mark_successful_deliveries",
    "run_count_channel_safely",
]
