# =============================================================================
# 모듈 설명: activity 서비스 파사드(공용 진입점)를 제공합니다.
# - 주요 대상: get_recent_activity_payload, record_activity_log
# - 불변 조건: 구현은 services/* 모듈로 위임합니다.
# =============================================================================

"""Activity 도메인 서비스 파사드입니다."""

from __future__ import annotations

from .activity_logs import get_recent_activity_payload, record_activity_log

__all__ = ["get_recent_activity_payload", "record_activity_log"]
