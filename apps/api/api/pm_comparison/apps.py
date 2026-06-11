# =============================================================================
# 모듈: PM SPIDER 앱 설정
# 주요 클래스: PmComparisonConfig
# 주요 가정: PM SPIDER는 파일 기반 조회 기능으로 동작합니다.
# =============================================================================
from __future__ import annotations

from django.apps import AppConfig


class PmComparisonConfig(AppConfig):
    """PM SPIDER 도메인 앱 설정입니다."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "api.pm_comparison"
