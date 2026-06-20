"""mes_eqp_mapping_info 앱 설정입니다."""

from __future__ import annotations

from django.apps import AppConfig


class MesEqpMappingInfoConfig(AppConfig):
    """mes_eqp_mapping_info 테이블 앱 설정입니다."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "api.data_movement.mes_eqp_mapping_info"
