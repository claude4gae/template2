# =============================================================================
# 모듈 설명: account 서비스 공용 유틸리티를 제공합니다.
# - 주요 대상: 관리자 권한 판별, 그룹 관리 권한 확인
# - 불변 조건: user 객체는 Django 사용자 모델 인터페이스를 따릅니다.
# =============================================================================

"""계정 서비스 공용 유틸리티 함수 모음.

- 주요 대상: 관리자 권한 판별, 그룹 관리 권한 확인
- 주요 엔드포인트/클래스: 없음(내부 헬퍼 제공)
- 가정/불변 조건: user 객체는 Django 사용자 모델을 따른다
"""
from __future__ import annotations

from typing import Any, Iterable

from .. import selectors
from ..models import UserSdwtProdAccess


def _normalize_user_sdwt_prod(value: Any) -> str:
    """user_sdwt_prod 값을 공백 제거 기준으로 정규화합니다.

    입력:
    - value: 원본 값

    반환:
    - str: 정규화된 문자열(없으면 빈 문자열)

    부작용:
    - 없음

    오류:
    - 없음
    """

    if not isinstance(value, str):
        return ""
    return value.strip()


def _normalize_user_sdwt_lookup_key(value: Any) -> str:
    """대소문자 비구분 비교용 user_sdwt_prod 키를 생성합니다.

    입력:
    - value: 원본 값

    반환:
    - str: casefold 기준 비교 키(없으면 빈 문자열)

    부작용:
    - 없음

    오류:
    - 없음
    """

    normalized = _normalize_user_sdwt_prod(value)
    if not normalized:
        return ""
    return normalized.casefold()


def _same_user_sdwt_prod(left: Any, right: Any) -> bool:
    """두 user_sdwt_prod 값이 대소문자 비구분으로 같은지 확인합니다.

    입력:
    - left: 비교 대상 1
    - right: 비교 대상 2

    반환:
    - bool: 같은 값 여부

    부작용:
    - 없음

    오류:
    - 없음
    """

    left_key = _normalize_user_sdwt_lookup_key(left)
    right_key = _normalize_user_sdwt_lookup_key(right)
    return bool(left_key and right_key and left_key == right_key)


def _build_user_sdwt_display_map(values: Iterable[Any]) -> dict[str, str]:
    """case-insensitive 비교용 lookup key → 표시값 매핑을 생성합니다.

    입력:
    - values: 원본 값 iterable

    반환:
    - dict[str, str]: lookup key → 공백 제거된 표시값

    부작용:
    - 없음

    오류:
    - 없음
    """

    display_map: dict[str, str] = {}
    for value in values:
        normalized = _normalize_user_sdwt_prod(value)
        lookup_key = _normalize_user_sdwt_lookup_key(normalized)
        if normalized and lookup_key and lookup_key not in display_map:
            display_map[lookup_key] = normalized
    return display_map


def _is_privileged_user(user: Any) -> bool:
    """superuser/staff 여부를 반환합니다.

    입력:
    - user: Django 사용자 객체

    반환:
    - bool: 관리자 여부

    부작용:
    - 없음

    오류:
    - 없음
    """

    return bool(getattr(user, "is_superuser", False) or getattr(user, "is_staff", False))


def _user_can_manage_user_sdwt_prod(*, user: Any, user_sdwt_prod: str) -> bool:
    """사용자가 user_sdwt_prod 그룹을 관리할 권한이 있는지 반환합니다.

    입력:
    - user: Django 사용자 객체
    - user_sdwt_prod: 소속 식별자

    반환:
    - bool: 관리 권한 여부

    부작용:
    - 없음

    오류:
    - 없음
    """

    # -----------------------------------------------------------------------------
    # 1) 관리자 권한 우선 처리
    # -----------------------------------------------------------------------------
    if _is_privileged_user(user):
        return True
    # -----------------------------------------------------------------------------
    # 2) 명시적 권한 확인
    # -----------------------------------------------------------------------------
    return selectors.user_has_manage_permission(user=user, user_sdwt_prod=user_sdwt_prod)


def _user_can_approve_affiliation_change(*, user: Any, target_user_sdwt_prod: str) -> bool:
    """사용자가 소속 변경을 승인할 수 있는지 반환합니다.

    입력:
    - user: Django 사용자 객체
    - target_user_sdwt_prod: 승인 대상 소속 값

    반환:
    - bool: 승인 가능 여부

    부작용:
    - 없음

    오류:
    - 없음
    """

    # -----------------------------------------------------------------------------
    # 1) 슈퍼유저/스태프는 항상 승인 가능
    # -----------------------------------------------------------------------------
    if _is_privileged_user(user):
        return True

    # -----------------------------------------------------------------------------
    # 2) 역할 기반 승인 권한 확인
    # -----------------------------------------------------------------------------
    normalized_target = _normalize_user_sdwt_prod(target_user_sdwt_prod)
    access = selectors.get_access_row_for_user_and_prod(
        user=user,
        user_sdwt_prod=normalized_target,
    )
    if not access:
        return False

    return access.role in {
        UserSdwtProdAccess.Roles.MEMBER,
        UserSdwtProdAccess.Roles.MANAGER,
    }
