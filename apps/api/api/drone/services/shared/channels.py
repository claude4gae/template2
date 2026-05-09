# =============================================================================
# 모듈: Drone 채널 스키마 상수
# 주요 기능: delivery 채널 키 단일화
# 주요 가정: 채널 키는 jira/messenger/mail 3개로 고정됩니다.
# =============================================================================
"""Drone 채널 키 상수 모듈."""

from __future__ import annotations

DRONE_SOP_DELIVERY_CHANNELS: tuple[str, ...] = ("jira", "messenger", "mail")

__all__ = [
    "DRONE_SOP_DELIVERY_CHANNELS",
]
