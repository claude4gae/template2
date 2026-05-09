# =============================================================================
# 모듈 설명: 활동 로그 직렬화 유틸을 제공합니다.
# - 주요 함수: serialize_activity_log
# - 불변 조건: API 응답에서 내부 브리지 IP는 제외합니다.
# =============================================================================
from __future__ import annotations

from typing import Any

from django.core.exceptions import ObjectDoesNotExist

from .models import ActivityLog

INTERNAL_BRIDGE_REMOTE_ADDR = "172.18.0.1"


def _get_user_role(user: Any | None) -> Any | None:
    """사용자 프로필 role 값을 안전하게 반환합니다."""

    if user is None:
        return None

    try:
        return getattr(user.profile, "role", None)
    except ObjectDoesNotExist:
        # 프로필이 없는 사용자는 예외 대신 None으로 처리합니다.
        return None


def _serialize_metadata(metadata: Any) -> Any:
    """응답에 노출할 ActivityLog metadata를 정리합니다."""

    normalized_metadata = metadata or {}
    if (
        isinstance(normalized_metadata, dict)
        and normalized_metadata.get("remote_addr") == INTERNAL_BRIDGE_REMOTE_ADDR
    ):
        # 도커 브리지 내부 IP는 의미가 없으므로 응답에서 제외합니다.
        return {
            key: value
            for key, value in normalized_metadata.items()
            if key != "remote_addr"
        }

    return normalized_metadata


def serialize_activity_log(entry: ActivityLog) -> dict[str, Any]:
    """ActivityLog 모델을 API 응답 형식으로 직렬화합니다.

    입력:
    - entry: ActivityLog 인스턴스

    반환:
    - dict[str, Any]: 활동 로그 API 응답 dict

    부작용:
    - 없음(읽기 전용 변환)

    오류:
    - 없음
    """

    user = entry.user
    username = user.get_username() if user else None

    return {
        "id": entry.id,
        "user": username,
        "role": _get_user_role(user),
        "action": entry.action,
        "path": entry.path,
        "method": entry.method,
        "status": entry.status_code,
        "metadata": _serialize_metadata(entry.metadata),
        "timestamp": entry.created_at.isoformat(),
    }


__all__ = ["serialize_activity_log"]
