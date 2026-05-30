"""m_tkin_prevent 앱 설정입니다."""

from __future__ import annotations

from django.apps import AppConfig


class MTkinPreventConfig(AppConfig):
    """m_tkin_prevent 테이블 앱 설정입니다."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "api.data_movement.m_tkin_prevent"
