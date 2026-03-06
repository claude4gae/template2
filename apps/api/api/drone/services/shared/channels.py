# =============================================================================
# 모듈: Drone 채널 스키마 상수
# 주요 기능: 채널 키/전송 필드/사유 필드 매핑 단일화
# 주요 가정: 채널 키는 jira/messenger/mail 3개로 고정됩니다.
# =============================================================================
"""Drone 채널 키/필드 매핑 상수 모듈."""

from __future__ import annotations

SEND_FIELD_BY_CHANNEL: dict[str, str] = {
    "jira": "send_jira",
    "messenger": "send_messenger",
    "mail": "send_mail",
}

REASON_FIELD_BY_SEND_FIELD: dict[str, str] = {
    "send_jira": "jira_reason",
    "send_messenger": "messenger_reason",
    "send_mail": "mail_reason",
}

__all__ = [
    "REASON_FIELD_BY_SEND_FIELD",
    "SEND_FIELD_BY_CHANNEL",
]
