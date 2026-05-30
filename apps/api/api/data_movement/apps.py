"""data_movement coordinator 앱 설정입니다."""

from __future__ import annotations

from django.apps import AppConfig


class DataMovementConfig(AppConfig):
    """data_movement API coordinator 앱 설정입니다."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "api.data_movement"
