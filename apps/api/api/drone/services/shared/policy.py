# =============================================================================
# 모듈: Drone SOP 알림 정책
# 주요 기능: target_user_sdwt_prod 누락 행의 delivery 실패 처리
# 주요 가정: 누락된 대상은 channel delivery 실패 사유로 기록해 자동 재처리 후보에서 제외합니다.
# =============================================================================
"""Drone SOP 알림 정책 유틸리티."""

from __future__ import annotations

from typing import Sequence

from django.db import transaction

from ...models import DroneSopDelivery

# 채널 상태 사유 코드
REASON_DISABLED_BY_POLICY = "disabled_by_policy"
REASON_TARGET_MISSING = "target_missing"
REASON_CONFIG_MISSING = "config_missing"
REASON_CHANNEL_CONFIG_MISSING = "channel_config_missing"
REASON_CHANNEL_CONFIG_INVALID = "channel_config_invalid"
REASON_TEMPLATE_MISSING = "template_missing"
REASON_RECEIVER_NOT_FOUND = "receiver_not_found"
REASON_SEND_FAILED = "send_failed"

_ALLOWED_CHANNELS = frozenset(
    {
        DroneSopDelivery.Channels.JIRA,
        DroneSopDelivery.Channels.MESSENGER,
        DroneSopDelivery.Channels.MAIL,
    }
)


def _normalize_channels(channels: Sequence[str]) -> list[str]:
    """허용 delivery 채널 목록만 중복 없이 정규화합니다."""

    if not channels:
        return []
    normalized: list[str] = []
    for channel in channels:
        if channel in _ALLOWED_CHANNELS and channel not in normalized:
            normalized.append(channel)
    return normalized


# =============================================================================
# 누락 대상 실패 처리
# =============================================================================

def mark_missing_target_as_failed(
    *,
    sop_ids: Sequence[int],
    channels: Sequence[str],
) -> None:
    """target_user_sdwt_prod 미확정 SOP를 delivery 실패로 처리합니다.

    인자:
        sop_ids: DroneSOP ID 목록.
        channels: 실패 처리할 delivery 채널 목록.

    반환:
        없음.

    부작용:
        누락 대상용 delivery snapshot을 실패 상태로 생성/갱신합니다.
    """

    # -----------------------------------------------------------------------------
    # 1) 입력 정규화
    # -----------------------------------------------------------------------------
    if not sop_ids:
        return

    normalized_channels = _normalize_channels(channels)
    if not normalized_channels:
        return

    # -----------------------------------------------------------------------------
    # 2) 누락 대상 delivery row 생성/갱신
    # -----------------------------------------------------------------------------
    with transaction.atomic():
        delivery_rows = [
            DroneSopDelivery(
                sop_id=sop_id,
                channel=channel,
                status=DroneSopDelivery.Statuses.FAILED,
                reason=REASON_TARGET_MISSING,
            )
            for sop_id in sop_ids
            if isinstance(sop_id, int) and sop_id > 0
            for channel in normalized_channels
        ]
        if not delivery_rows:
            return
        DroneSopDelivery.objects.bulk_create(delivery_rows, ignore_conflicts=True)
        DroneSopDelivery.objects.filter(
            sop_id__in=[row.sop_id for row in delivery_rows],
            channel__in=normalized_channels,
        ).update(
            status=DroneSopDelivery.Statuses.FAILED,
            reason=REASON_TARGET_MISSING,
        )


__all__ = [
    "REASON_CHANNEL_CONFIG_INVALID",
    "REASON_CHANNEL_CONFIG_MISSING",
    "REASON_CONFIG_MISSING",
    "REASON_DISABLED_BY_POLICY",
    "REASON_TARGET_MISSING",
    "REASON_RECEIVER_NOT_FOUND",
    "REASON_SEND_FAILED",
    "REASON_TEMPLATE_MISSING",
    "mark_missing_target_as_failed",
]
