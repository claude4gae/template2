# =============================================================================
# 모듈 설명: observer 앱 설정을 제공합니다.
# - 주요 클래스: ObserverConfig
# - 불변 조건: 앱 이름은 api.observer 입니다.
# =============================================================================

"""observer 앱 설정 모듈."""
from __future__ import annotations

from django.apps import AppConfig


class ObserverConfig(AppConfig):
    """observer 도메인 앱 설정 클래스입니다."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "api.observer"
