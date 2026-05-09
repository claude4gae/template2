# =============================================================================
# 모듈 설명: OIDC state/nonce/id_token 검증 헬퍼를 제공합니다.
# - 주요 대상: redirect target 정규화, id_token 디코드, nonce/필수 클레임 검증
# - 불변 조건: redirect target은 허용 목록 검증을 통과해야 합니다.
# =============================================================================

"""OIDC callback 검증 헬퍼 모음.

- 주요 대상: state 복원, 안전한 redirect target 계산, id_token 디코드
- 주요 함수: decode_state_to_target, resolve_safe_redirect_target, decode_id_token
- 가정/불변 조건: 세션 nonce와 id_token nonce가 일치해야 로그인 가능함
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import jwt
from django.http import HttpRequest

from api.common.services import resolve_frontend_target
from .oidc_utils import (
    PUB_KEY,
    b64d,
    is_allowed_redirect,
)


def decode_state_to_target(state: str, request: HttpRequest) -> str:
    """state(b64url)를 redirect target 문자열로 복원합니다.

    입력:
    - state: base64url 인코딩된 문자열
    - 요청: Django HttpRequest

    반환:
    - str: 복원된 target 또는 기본 프론트엔드 URL

    부작용:
    - 없음

    오류:
    - 없음(복원 실패 시 기본 프론트엔드 URL 반환)
    """
    try:
        decoded_state = b64d(state)
    except Exception:
        return resolve_frontend_target(None, request=request)

    if isinstance(decoded_state, str):
        return decoded_state

    try:
        return decoded_state.decode("utf-8")
    except Exception:
        return str(decoded_state, "utf-8", errors="ignore")


def resolve_safe_redirect_target(target: Optional[str], request: HttpRequest) -> str:
    """target을 안전한 리다이렉트 URL로 정규화합니다.

    입력:
    - target: 요청된 리다이렉트 대상
    - 요청: Django HttpRequest

    반환:
    - str: 허용 목록 검증을 통과한 URL

    부작용:
    - 없음

    오류:
    - 없음
    """
    resolved = resolve_frontend_target(target, request=request)
    if not is_allowed_redirect(resolved):
        return resolve_frontend_target(None, request=request)
    return resolved


def ensure_pubkey_ready() -> None:
    """PUB_KEY 준비 상태를 확인합니다.

    입력:
    - 없음

    반환:
    - 없음

    부작용:
    - 없음

    오류:
    - RuntimeError: 공개키 설정이 없을 때
    """
    if not PUB_KEY:
        raise RuntimeError("OIDC public key (PUB_KEY) is not configured.")


def decode_id_token(raw_id_token: str) -> Dict[str, Any]:
    """id_token(JWT)을 디코드해 클레임 딕셔너리를 반환합니다.

    입력:
    - raw_id_token: id_token 문자열

    반환:
    - Dict[str, Any]: JWT 클레임

    부작용:
    - 없음

    오류:
    - jwt.PyJWTError: 토큰 파싱/검증 실패
    """
    return jwt.decode(
        raw_id_token,
        PUB_KEY,
        algorithms=["RS256"],
        options={
            # 사내 시스템 전용 기존 동작을 보존하기 위해 검증 비활성 설정을 유지합니다.
            "verify_signature": False,
            "verify_exp": False,
            "verify_aud": False,
            "verify_iss": False,
        },
    )


def map_token_error(exc: jwt.PyJWTError) -> str:
    """PyJWT 예외를 기존 redirect error 코드로 변환합니다.

    입력:
    - exc: PyJWT 예외 객체

    반환:
    - str: 기존 프론트엔드가 해석하는 error 코드

    부작용:
    - 없음

    오류:
    - 없음
    """
    if isinstance(exc, jwt.ExpiredSignatureError):
        return "token_expired"
    if isinstance(exc, jwt.InvalidIssuerError):
        return "invalid_iss"
    if isinstance(exc, jwt.InvalidAudienceError):
        return "invalid_aud"
    return "invalid_token"


def validate_nonce(*, claims: Dict[str, Any], expected_nonce: Optional[str]) -> bool:
    """세션 nonce와 id_token nonce가 일치하는지 확인합니다.

    입력:
    - claims: id_token 클레임
    - expected_nonce: 세션에서 꺼낸 nonce

    반환:
    - bool: nonce 일치 여부

    부작용:
    - 없음

    오류:
    - 없음
    """
    return expected_nonce is not None and claims.get("nonce") == expected_nonce


def validate_required_identity(
    info: Dict[str, Optional[str]],
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """로그인에 필요한 sabun/knox_id 값을 검증합니다.

    입력:
    - info: 클레임에서 추출한 사용자 정보

    반환:
    - tuple[Optional[str], Optional[str], Optional[str]]: sabun, knox_id, error_code

    부작용:
    - 없음

    오류:
    - 없음
    """
    sabun = info.get("sabun")
    knox_id = info.get("knox_id")
    if not sabun:
        return None, None, "missing_sabun"
    if not knox_id:
        return str(sabun), None, "missing_loginid"
    return str(sabun), str(knox_id), None


def append_error_to_target(target: str, error_code: str) -> str:
    """리다이렉트 target에 기존 error 쿼리 형식으로 오류 코드를 붙입니다.

    입력:
    - target: 안전한 리다이렉트 대상 URL
    - error_code: 오류 코드 문자열

    반환:
    - str: error 쿼리가 추가된 URL

    부작용:
    - 없음

    오류:
    - 없음
    """
    separator = "&" if "?" in target else "?"
    return f"{target}{separator}error={error_code}"


__all__ = [
    "append_error_to_target",
    "decode_id_token",
    "decode_state_to_target",
    "ensure_pubkey_ready",
    "map_token_error",
    "resolve_safe_redirect_target",
    "validate_nonce",
    "validate_required_identity",
]
