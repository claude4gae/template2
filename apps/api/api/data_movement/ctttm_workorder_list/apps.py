"""ctttm_workorder_list 앱 설정입니다."""

from __future__ import annotations

from django.apps import AppConfig


class CtttmWorkorderListConfig(AppConfig):
    """ctttm_workorder_list 테이블 앱 설정입니다."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "api.data_movement.ctttm_workorder_list"
