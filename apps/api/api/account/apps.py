# =============================================================================
# 모듈 설명: account 앱 설정과 초기 시그널/기본 슈퍼유저 보정 로직을 제공합니다.
# - 주요 클래스: AccountConfig
# - 불변 조건: ready 단계에서 시그널 등록과 보정만 수행합니다.
# =============================================================================

from __future__ import annotations

import os

from django.apps import AppConfig
from django.db import IntegrityError, OperationalError, ProgrammingError, connection


class AccountConfig(AppConfig):
    """Account 도메인 앱 설정 및 사용자 생성 시 프로필 시그널을 등록합니다."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "api.account"

    def ready(self) -> None:
        """앱 준비 시 시그널 등록과 기본 슈퍼유저 보정을 수행합니다.

        입력:
        - 없음

        반환:
        - 없음

        부작용:
        - 사용자 생성 시 프로필 생성 시그널 등록
        - 기본 슈퍼유저 생성 시도

        오류:
        - 없음(내부에서 방어적으로 처리)
        """
        # -----------------------------------------------------------------------------
        # 1) 사용자 생성 시 프로필 생성 시그널 연결
        # -----------------------------------------------------------------------------
        from django.contrib.auth import get_user_model
        from django.db.models.signals import post_save

        from api.account.services import ensure_user_profile

        def create_profile(sender, instance, created: bool, **kwargs) -> None:
            """사용자 생성/knox_id 갱신 시 계정 부가 데이터를 보장합니다.

            입력:
            - sender: Django 시그널 발신 모델
            - instance: 저장된 사용자 인스턴스
            - created: 신규 생성 여부
            - **kwargs: 시그널 추가 인자

            반환:
            - 없음

            부작용:
            - 사용자 프로필 생성 가능
            - 외부 Drone SOP 수신인 row 승격 가능

            오류:
            - 없음
            """
            if created:
                ensure_user_profile(instance)
            update_fields = kwargs.get("update_fields")
            if not created and update_fields is not None and "knox_id" not in update_fields:
                return
            try:
                from api.drone import services as drone_services

                drone_services.promote_drone_sop_external_recipients_for_user(user=instance)
            except (OperationalError, ProgrammingError):
                return

        post_save.connect(
            create_profile,
            sender=get_user_model(),
            dispatch_uid="account_create_profile",
        )

        # -----------------------------------------------------------------------------
        # 2) 기본 슈퍼유저 보정 실행
        # -----------------------------------------------------------------------------
        self._ensure_default_superuser()

    def _ensure_default_superuser(self) -> None:
        """기본 슈퍼유저가 없을 때 환경변수 기반으로 생성합니다.

        입력:
        - 없음

        반환:
        - 없음

        부작용:
        - 기본 슈퍼유저 생성 시도

        오류:
        - 없음(테이블 미존재/무결성 오류는 조용히 반환)
        """
        from django.contrib.auth import get_user_model

        def env_or_default(key: str, default: str) -> str:
            """환경변수에서 값을 읽고 없으면 기본값을 반환합니다.

            입력:
            - key: 환경변수 키
            - default: 기본값

            반환:
            - str: 환경변수 값 또는 기본값

            부작용:
            - 없음

            오류:
            - 없음
            """
            value = os.environ.get(key)
            if value is None:
                return default
            value = value.strip()
            return value or default

        # -----------------------------------------------------------------------------
        # 1) 테이블 존재 여부 확인
        # -----------------------------------------------------------------------------
        UserModel = get_user_model()
        try:
            table_names = connection.introspection.table_names()
        except (OperationalError, ProgrammingError):
            return

        if UserModel._meta.db_table not in table_names:
            return

        # -----------------------------------------------------------------------------
        # 2) 대상 sabun 중복 확인
        # -----------------------------------------------------------------------------
        sabun = env_or_default("DJANGO_SUPERUSER_SABUN", "00000000")
        if UserModel.objects.filter(sabun=sabun).exists():
            return

        # -----------------------------------------------------------------------------
        # 3) 기본 슈퍼유저 생성 시도
        # -----------------------------------------------------------------------------
        try:
            UserModel.objects.create_superuser(
                sabun=sabun,
                password=env_or_default("DJANGO_SUPERUSER_PASSWORD", "dkssud123!"),
                username=env_or_default("DJANGO_SUPERUSER_USERNAME", "admin"),
                knox_id="admin",
                email=env_or_default("DJANGO_SUPERUSER_EMAIL", "etch_mail_collector@samsung.com"),
            )
        except IntegrityError:
            return
