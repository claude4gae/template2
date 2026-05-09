# =============================================================================
# 모듈 설명: OIDC 클레임을 사용자 정보로 변환하고 저장합니다.
# - 주요 대상: 클레임 매핑, 사용자 생성/갱신
# - 불변 조건: sabun은 사용자 식별 기준이며 knox_id는 필수 로그인 식별자입니다.
# =============================================================================

"""OIDC 클레임 기반 사용자 생성/갱신 서비스.

- 주요 대상: 클레임 필드 매핑, 사용자 upsert
- 주요 함수: extract_user_info_from_claims, upsert_user_from_claims
- 가정/불변 조건: sabun은 사용자 조회 키로 사용하고 knox_id는 비어 있을 수 없음
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

import api.auth.selectors as auth_selectors


def extract_user_info_from_claims(claims: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """ADFS 클레임을 사용자 모델 필드로 매핑해 반환합니다.

    입력:
    - claims: id_token에서 추출한 클레임 딕셔너리

    반환:
    - Dict[str, Optional[str]]: 사용자 필드 매핑 결과

    부작용:
    - 없음

    오류:
    - 없음
    """
    claim_to_field = {
        "loginid": "knox_id",
        "userid": "avatarid",
        "sabun": "sabun",
        "username": "username",
        "username_en": "username_en",
        "first_name": "first_name",
        "last_name": "last_name",
        "givenname": "givenname",
        "surname": "surname",
        "deptname": "department",
        "deptid": "deptid",
        "mail": "email",
        "grdName": "grd_name",
        "grdname_en": "grdname_en",
        "busname": "busname",
        "intcode": "intcode",
        "intname": "intname",
        "origincomp": "origincomp",
        "employeetype": "employeetype",
    }

    info: Dict[str, Optional[str]] = {}
    for claim_key, field_name in claim_to_field.items():
        raw = claims.get(claim_key)
        value = str(raw).strip() if raw is not None else ""
        info[field_name] = value or None

    # 한글 username만 있는 기존 SSO 응답에서도 first_name/last_name을 유지합니다.
    username = info.get("username") or ""
    if username and (not info.get("first_name") or not info.get("last_name")):
        trimmed = username.strip()
        if trimmed:
            if len(trimmed) >= 2:
                info["last_name"] = info.get("last_name") or trimmed[:1]
                info["first_name"] = info.get("first_name") or trimmed[1:]
            else:
                info["first_name"] = info.get("first_name") or trimmed

    return info


def _apply_user_updates(*, user: Any, candidate_updates: Dict[str, Optional[str]]) -> List[str]:
    """사용자 필드 변경사항을 적용하고 업데이트 필드 목록을 반환합니다.

    입력:
    - user: Django 사용자 객체
    - candidate_updates: 변경 후보 필드/값 딕셔너리

    반환:
    - List[str]: 변경된 필드 목록

    부작용:
    - user 객체 필드 갱신(저장은 호출자가 수행)

    오류:
    - 없음
    """
    concrete_field_names = {field.name for field in user._meta.concrete_fields}
    update_fields: List[str] = []
    for field_name, value in candidate_updates.items():
        if not value:
            continue
        if field_name not in concrete_field_names:
            continue
        if getattr(user, field_name) == value:
            continue
        setattr(user, field_name, value)
        update_fields.append(field_name)

    return update_fields


def upsert_user_from_claims(
    *,
    info: Dict[str, Optional[str]],
    sabun: str,
    knox_id: str,
) -> tuple[Any, bool]:
    """클레임 정보 기반으로 사용자를 생성/갱신합니다.

    입력:
    - info: 클레임에서 추출한 사용자 정보
    - sabun: 사번 문자열
    - knox_id: 로그인 ID 문자열

    반환:
    - tuple[Any, bool]: (사용자 객체, 생성 여부)

    부작용:
    - 사용자 생성/갱신

    오류:
    - IntegrityError: 사용자 생성 경합 발생 시 재시도 후에도 실패
    """
    normalized_sabun = str(sabun)
    normalized_knox_id = str(knox_id)
    UserModel = get_user_model()
    concrete_field_names = {field.name for field in UserModel._meta.concrete_fields}
    defaults = {
        key: value
        for key, value in info.items()
        if key != "sabun" and key in concrete_field_names
    }
    defaults["knox_id"] = normalized_knox_id

    with transaction.atomic():
        user = auth_selectors.get_user_by_sabun(sabun=normalized_sabun)
        created = False
        if user is None:
            try:
                user = UserModel.objects.create(sabun=normalized_sabun, **defaults)
                created = True
            except IntegrityError:
                user = auth_selectors.get_user_by_sabun(sabun=normalized_sabun)
                if user is None:
                    raise

        candidate_updates = {**info, "knox_id": normalized_knox_id}
        candidate_updates.pop("sabun", None)
        update_fields = _apply_user_updates(user=user, candidate_updates=candidate_updates)
        if created or update_fields:
            user.save(update_fields=update_fields or None)

    return user, created


__all__ = [
    "extract_user_info_from_claims",
    "upsert_user_from_claims",
]
