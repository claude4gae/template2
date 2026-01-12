# =============================================================================
# 모듈 설명: 사용자 관련 서비스 헬퍼를 제공합니다.
# - 주요 대상: ensure_user_profile, resolve_target_user
# - 불변 조건: user가 None이면 프로필을 생성할 수 없습니다.
# =============================================================================

"""사용자 관련 서비스 헬퍼 모음.

- 주요 대상: 프로필 보장, 대상 사용자 조회
- 주요 엔드포인트/클래스: ensure_user_profile, resolve_target_user
- 가정/불변 조건: user가 None이면 프로필 생성 불가
"""
from __future__ import annotations

from typing import Any

from django.db import IntegrityError, transaction

from .. import selectors
from ..models import UserProfile


def ensure_user_profile(user: Any) -> UserProfile:
    """사용자 프로필(UserProfile)이 없으면 생성하고 반환합니다.

    입력:
    - user: Django 사용자 객체

    반환:
    - UserProfile: 프로필 객체

    부작용:
    - UserProfile 행 생성 가능

    오류:
    - ValueError: user가 None인 경우
    """

    # -----------------------------------------------------------------------------
    # 1) 입력 유효성 확인
    # -----------------------------------------------------------------------------
    if user is None:
        raise ValueError("user is required to ensure a profile exists")

    # -----------------------------------------------------------------------------
    # 2) 기존 프로필 조회 및 생성 처리
    # -----------------------------------------------------------------------------
    with transaction.atomic():
        profile = selectors.get_user_profile_by_user(user=user)
        if profile is None:
            try:
                profile = UserProfile.objects.create(user=user)
            except IntegrityError:
                profile = selectors.get_user_profile_by_user(user=user)
                if profile is None:
                    raise

    return profile


def get_user_by_knox_id(*, knox_id: str) -> Any | None:
    """knox_id로 사용자를 조회합니다.

    입력:
    - knox_id: 사용자 knox_id 문자열

    반환:
    - Any | None: 사용자 객체 또는 None

    부작용:
    - 없음

    오류:
    - 없음
    """

    normalized_knox_id = (knox_id or "").strip()
    if not normalized_knox_id:
        return None
    return selectors.get_user_by_knox_id(knox_id=normalized_knox_id)


def resolve_target_user(
    *,
    target_id: object,
    target_knox_id: object,
) -> Any | None:
    """id 또는 knox_id로 대상 사용자를 조회합니다.

    입력:
    - target_id: 사용자 id 후보 값
    - target_knox_id: knox_id 후보 값

    반환:
    - Any | None: 대상 사용자 또는 None

    부작용:
    - 없음

    오류:
    - 없음
    """

    target: Any | None = None

    # -----------------------------------------------------------------------------
    # 1) id 기반 조회
    # -----------------------------------------------------------------------------
    if target_id not in (None, ""):
        try:
            target = selectors.get_user_by_id(user_id=int(target_id))
        except (TypeError, ValueError):
            target = None

    # -----------------------------------------------------------------------------
    # 2) knox_id 기반 폴백
    # -----------------------------------------------------------------------------
    if target is None and isinstance(target_knox_id, str) and target_knox_id.strip():
        target = selectors.get_user_by_knox_id(knox_id=target_knox_id.strip())

    return target
