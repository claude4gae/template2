"""eqp_status_chg 앱 설정입니다."""

from __future__ import annotations

from django.apps import AppConfig


class EqpStatusChgConfig(AppConfig):
    """eqp_status_chg data movement 앱 설정 클래스입니다."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "api.data_movement.eqp_status_chg"
