"""로컬 개발용 더미 계정과 현재 소속을 준비하는 management command입니다."""

from __future__ import annotations

import os
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from api.account.models import UserCurrentAffiliation
from api.account.services import (
    ensure_user_profile,
    set_current_affiliation_for_user,
    sync_external_affiliations,
)


DEFAULT_DUMMY_EMAIL = "dummy.user@example.com"
DEFAULT_DUMMY_NAME = "Dummy User"
DEFAULT_DUMMY_SABUN = "S000001"
DEFAULT_DUMMY_LOGINID = "dummy.user"
DEFAULT_DUMMY_DEPARTMENT = "Development"
DEFAULT_DUMMY_DEPT_ID = "D000000"
DEFAULT_DUMMY_LINE = "DEV"
DEFAULT_DUMMY_USER_SDWT_PROD = "DEV_DUMMY_USER_SDWT"


def _env_or_default(name: str, fallback: str) -> str:
    """환경변수 문자열을 공백 제거 후 반환하고, 비어 있으면 기본값을 사용합니다."""

    value = os.getenv(name)
    if value is None:
        return fallback
    normalized = value.strip()
    return normalized or fallback


def _split_display_name(name: str) -> tuple[str, str]:
    """Django User의 first_name/last_name에 넣을 표시 이름을 나눕니다."""

    normalized = (name or "").strip()
    if not normalized:
        return "", ""
    parts = normalized.split(maxsplit=1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


class Command(BaseCommand):
    """더미 ADFS 사용자와 앱 소속을 idempotent하게 생성합니다."""

    help = "Seed local dummy ADFS user and current account affiliation."

    def add_arguments(self, parser: CommandParser) -> None:
        """테스트와 로컬 override를 위한 옵션을 등록합니다."""

        parser.add_argument("--email", default=_env_or_default("DUMMY_ADFS_EMAIL", DEFAULT_DUMMY_EMAIL))
        parser.add_argument("--name", default=_env_or_default("DUMMY_ADFS_NAME", DEFAULT_DUMMY_NAME))
        parser.add_argument("--sabun", default=_env_or_default("DUMMY_ADFS_SABUN", DEFAULT_DUMMY_SABUN))
        parser.add_argument("--knox-id", default=_env_or_default("DUMMY_ADFS_LOGINID", DEFAULT_DUMMY_LOGINID))
        parser.add_argument("--department", default=_env_or_default("DUMMY_ADFS_DEPT", DEFAULT_DUMMY_DEPARTMENT))
        parser.add_argument("--dept-id", default=_env_or_default("DUMMY_ADFS_DEPTID", DEFAULT_DUMMY_DEPT_ID))
        parser.add_argument("--line", default=_env_or_default("DUMMY_ACCOUNT_LINE", DEFAULT_DUMMY_LINE))
        parser.add_argument(
            "--user-sdwt-prod",
            default=_env_or_default("DUMMY_ACCOUNT_USER_SDWT_PROD", DEFAULT_DUMMY_USER_SDWT_PROD),
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """더미 사용자, 프로필, 외부 스냅샷, 현재 소속을 준비합니다."""

        email = str(options["email"]).strip()
        name = str(options["name"]).strip()
        sabun = str(options["sabun"]).strip()
        knox_id = str(options["knox_id"]).strip()
        department = str(options["department"]).strip()
        dept_id = str(options["dept_id"]).strip()
        line = str(options["line"]).strip()
        user_sdwt_prod = str(options["user_sdwt_prod"]).strip()

        missing = [
            field_name
            for field_name, value in {
                "email": email,
                "name": name,
                "sabun": sabun,
                "knox_id": knox_id,
                "department": department,
                "line": line,
                "user_sdwt_prod": user_sdwt_prod,
            }.items()
            if not value
        ]
        if missing:
            raise ValueError(f"Missing dummy account seed values: {', '.join(missing)}")

        first_name, last_name = _split_display_name(name)
        UserModel = get_user_model()

        with transaction.atomic():
            user = UserModel.objects.filter(sabun=sabun).first()
            created = user is None
            if user is None:
                user = UserModel(sabun=sabun)
                user.set_unusable_password()

            user.knox_id = knox_id
            user.email = email
            user.username = name
            user.first_name = first_name
            user.last_name = last_name
            user.department = department
            user.deptid = dept_id
            user.is_active = True
            user.save()

            ensure_user_profile(user=user)
            set_current_affiliation_for_user(
                user=user,
                department=department,
                line=line,
                user_sdwt_prod=user_sdwt_prod,
                source=UserCurrentAffiliation.Sources.EXTERNAL_AUTO,
            )
            sync_external_affiliations(
                records=[
                    {
                        "knox_id": knox_id,
                        "username": name,
                        "department": department,
                        "user_sdwt_prod": user_sdwt_prod,
                    }
                ]
            )

        action = "created" if created else "updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"Dummy account {action}: sabun={sabun}, knox_id={knox_id}, user_sdwt_prod={user_sdwt_prod}"
            )
        )
