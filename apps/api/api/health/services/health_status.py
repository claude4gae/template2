# =============================================================================
# 모듈 설명: health 상태 응답 payload 생성 로직을 제공합니다.
# - 주요 함수: get_health_payload
# - 불변 조건: status는 항상 "ok"입니다.
# =============================================================================

from __future__ import annotations

from django.conf import settings

DEFAULT_APPLICATION_NAME = "template2-api"


def get_health_payload() -> dict[str, str]:
    """헬스 체크 응답 payload를 생성합니다.

    입력:
    - 없음

    반환:
    - dict[str, str]: status/application 정보를 담은 payload

    부작용:
    - 없음

    오류:
    - 없음
    """

    application_name = getattr(settings, "APPLICATION_NAME", None)
    if not isinstance(application_name, str) or not application_name.strip():
        application_name = DEFAULT_APPLICATION_NAME

    return {
        "status": "ok",
        "application": application_name,
    }
