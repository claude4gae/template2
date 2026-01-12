# =============================================================================
# 모듈 설명: 활동 로그 직렬화 유틸을 제공합니다.
# - 주요 함수: serialize_activity_log
# - 불변 조건: API 응답에서 내부 브리지 IP는 제외합니다.
# =============================================================================
from __future__ import annotations

from typing import Any

from django.core.exceptions import ObjectDoesNotExist

from .models import ActivityLog


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
    role = None
    if user:
        try:
            role = getattr(user.profile, "role", None)
        except ObjectDoesNotExist:
            # 프로필이 없는 사용자는 예외 대신 None으로 처리합니다.
            role = None

    metadata = entry.metadata or {}
    if isinstance(metadata, dict) and metadata.get("remote_addr") == "172.18.0.1":
        # 도커 브리지 내부 IP는 의미가 없으므로 응답에서 제외합니다.
        metadata = {key: value for key, value in metadata.items() if key != "remote_addr"}

    return {
        "id": entry.id,
        "user": username,
        "role": role,
        "action": entry.action,
        "path": entry.path,
        "method": entry.method,
        "status": entry.status_code,
        "metadata": metadata,
        "timestamp": entry.created_at.isoformat(),
    }


__all__ = ["serialize_activity_log"]
