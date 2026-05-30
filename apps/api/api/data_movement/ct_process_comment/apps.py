"""ct_process_comment 앱 설정입니다."""

from __future__ import annotations

from django.apps import AppConfig


class CtProcessCommentConfig(AppConfig):
    """ct_process_comment 테이블 앱 설정입니다."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "api.data_movement.ct_process_comment"
