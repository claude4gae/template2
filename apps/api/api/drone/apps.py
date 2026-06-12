# =============================================================================
# 모듈: 드론 앱 설정
# 주요 클래스: DroneConfig
# 주요 가정: 앱 라벨은 api.drone을 사용합니다.
# =============================================================================
from __future__ import annotations

from django.apps import AppConfig
from django.db import OperationalError, ProgrammingError


class DroneConfig(AppConfig):
    """Drone 도메인 앱 설정입니다."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "api.drone"

    def ready(self) -> None:
        """사용자 변경에 따른 Drone 도메인 후처리 시그널을 등록합니다."""

        from django.contrib.auth import get_user_model
        from django.db.models.signals import post_save

        def promote_external_recipients(sender, instance, created: bool, **kwargs) -> None:
            """사용자 생성/knox_id 갱신 시 외부 수신인 row를 실제 사용자로 승격합니다."""

            update_fields = kwargs.get("update_fields")
            if not created and update_fields is not None and "knox_id" not in update_fields:
                return
            try:
                from api.drone import services as drone_services

                drone_services.promote_drone_sop_external_recipients_for_user(user=instance)
            except (OperationalError, ProgrammingError):
                return

        post_save.connect(
            promote_external_recipients,
            sender=get_user_model(),
            dispatch_uid="drone_promote_external_recipients_for_user",
            weak=False,
        )
