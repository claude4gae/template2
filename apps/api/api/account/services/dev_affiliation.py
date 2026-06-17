# =============================================================================
# 모듈 설명: 로컬 dev 로그인 사용자의 기본 소속 보장 헬퍼를 제공합니다.
# - 주요 함수: ensure_dev_user_affiliation
# - 불변 조건: 명시적인 dev 자동 소속 flag가 있을 때만 DB를 변경합니다.
# =============================================================================

from __future__ import annotations

import os
from typing import Any

from ..models import UserCurrentAffiliation, UserSdwtProdAccess, UserSdwtProdChange
from .access import ensure_self_access
from .affiliations import set_current_affiliation_for_user


def _env(name: str, default: str = "") -> str:
    """환경변수 문자열 값을 공백 제거 후 반환합니다."""

    return (os.getenv(name) or default).strip()


def _env_enabled(name: str) -> bool:
    """환경변수 값이 활성화 의미인지 확인합니다."""

    return _env(name).lower() in {"1", "true", "yes", "on"}


def _dev_auto_affiliation_enabled() -> bool:
    """외부망 dev 자동 소속 보장 기능이 켜져 있는지 확인합니다."""

    return _env("ENVIRONMENT").lower() == "development" and _env_enabled("DEV_AUTO_AFFILIATION_ALLOWED")


def _prefixed(prefix: str, value: str) -> str:
    """dev 자동 소속 식별 prefix를 붙인 값을 반환합니다."""

    return f"{prefix}_{value}"


def ensure_dev_user_affiliation(*, user: Any) -> dict[str, object]:
    """외부망 dev에서 소속 없는 로그인 사용자에게 기본 개발 소속을 부여합니다.

    입력:
    - user: 인증된 Django 사용자 객체

    반환:
    - dict[str, object]: 적용 여부와 사유

    부작용:
    - dev 자동 소속 플래그가 켜진 경우에만 UserCurrentAffiliation/UserSdwtProdAccess를 보장합니다.

    오류:
    - 없음
    """

    if not user or not getattr(user, "is_authenticated", False):
        return {"applied": False, "reason": "anonymous"}
    if not _dev_auto_affiliation_enabled():
        return {"applied": False, "reason": "disabled"}

    current = (
        UserCurrentAffiliation.objects.filter(user=user)
        .select_related("affiliation")
        .order_by("id")
        .first()
    )
    current_user_sdwt_prod = (
        current.affiliation.user_sdwt_prod.strip()
        if current and current.affiliation and current.affiliation.user_sdwt_prod
        else ""
    )
    if current_user_sdwt_prod:
        return {
            "applied": False,
            "reason": "already_affiliated",
            "user_sdwt_prod": current_user_sdwt_prod,
        }

    has_pending_affiliation = UserSdwtProdChange.objects.filter(
        user=user,
        status=UserSdwtProdChange.Status.PENDING,
        applied=False,
    ).exists()
    if has_pending_affiliation:
        return {"applied": False, "reason": "pending_affiliation"}

    normalized_prefix = (_env("DEV_AUTO_AFFILIATION_PREFIX", "DEV") or "DEV").strip().upper()
    department = (getattr(user, "department", None) or _env("DUMMY_ADFS_DEPT", "Development") or "DEV").strip()
    line = f"{normalized_prefix}-L1"
    user_sdwt_prod = _prefixed(normalized_prefix, "ALPHA")

    set_current_affiliation_for_user(
        user=user,
        department=department,
        line=line,
        user_sdwt_prod=user_sdwt_prod,
        source=UserCurrentAffiliation.Sources.ADMIN_ASSIGNED,
    )
    ensure_self_access(user, role=UserSdwtProdAccess.Roles.MEMBER)
    return {
        "applied": True,
        "reason": "created",
        "department": department,
        "line": line,
        "user_sdwt_prod": user_sdwt_prod,
    }
