# =============================================================================
# 모듈 설명: ADFS OIDC 유틸리티와 검증 헬퍼를 제공합니다.
# - 주요 대상: 인증서 로드, thumbprint 계산, 리다이렉트 검증, nonce 처리
# - 불변 조건: OIDC 설정은 Django settings에서 제공됩니다.
# =============================================================================

"""ADFS OIDC 응답(id_token only) 검증을 위한 유틸리티 모음.

- 주요 대상: 인증서 로드, x5t 계산, 리다이렉트 안전성 검사, nonce 저장
- 주요 엔드포인트/클래스: 없음(함수형 헬퍼만 제공)
- 가정/불변 조건: OIDC 설정은 Django settings에서 제공됨
"""
from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from urllib.parse import urlparse

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from django.conf import settings
from django.http import HttpRequest

ADFS_AUTH_URL = settings.ADFS_AUTH_URL
ADFS_LOGOUT_URL = settings.ADFS_LOGOUT_URL
OIDC_CLIENT_ID = settings.OIDC_CLIENT_ID
ISSUER = settings.OIDC_ISSUER
REDIRECT_URI = settings.OIDC_REDIRECT_URI
CER_PATH = settings.ADFS_CER_PATH  # ADFS 토큰-서명 인증서(.cer, PEM 또는 DER)

# --------------------------
# 인증서 / 공개키
# --------------------------


def _read_certificate_bytes(path: str | Path) -> bytes:
    """인증서 파일을 읽어 바이트로 반환합니다.

    입력:
    - path: 인증서 파일 경로

    반환:
    - bytes: 인증서 바이트

    부작용:
    - 파일 시스템 읽기

    오류:
    - RuntimeError: 파일이 없거나 읽기 실패
    """

    # -----------------------------------------------------------------------------
    # 1) 파일 읽기 시도
    # -----------------------------------------------------------------------------
    try:
        return Path(path).expanduser().resolve(strict=True).read_bytes()
    except FileNotFoundError as exc:
        raise RuntimeError(f"OIDC public certificate not found: {path}") from exc
    except OSError as exc:
        raise RuntimeError(f"Failed to read OIDC certificate: {path}") from exc


def load_x509_cert(path: str | Path) -> x509.Certificate:
    """인증서(.cer)를 읽어 X.509 객체로 로드합니다.

    입력:
    - path: 인증서 파일 경로(PEM 또는 DER)

    반환:
    - x509.Certificate: 로드된 인증서 객체

    부작용:
    - 파일 시스템 읽기

    오류:
    - RuntimeError: 파일 읽기 실패
    - ValueError: PEM/DER 파싱 실패 시(내부에서 전환 시도)
    """
    data = _read_certificate_bytes(path)
    # -----------------------------------------------------------------------------
    # 1) PEM 파싱 시도
    # -----------------------------------------------------------------------------
    try:
        return x509.load_pem_x509_certificate(data, default_backend())
    except ValueError:
        # -----------------------------------------------------------------------------
        # 2) DER 파싱 폴백
        # -----------------------------------------------------------------------------
        return x509.load_der_x509_certificate(data, default_backend())


def compute_cert_thumbprint_x5t(cert: x509.Certificate) -> str:
    """인증서 thumbprint(x5t)을 계산합니다.

    입력:
    - cert: X.509 인증서 객체

    반환:
    - str: base64url(sha1(der)) 문자열

    부작용:
    - 없음

    오류:
    - 없음
    """
    # -----------------------------------------------------------------------------
    # 1) DER 바이트 추출
    # -----------------------------------------------------------------------------
    der = cert.public_bytes(encoding=x509.Encoding.DER)
    # -----------------------------------------------------------------------------
    # 2) SHA-1 해시 계산
    # -----------------------------------------------------------------------------
    sha1 = hashlib.sha1(der).digest()
    # -----------------------------------------------------------------------------
    # 3) base64url 인코딩
    # -----------------------------------------------------------------------------
    return base64.urlsafe_b64encode(sha1).rstrip(b"=").decode("ascii")


PUB_CERT = load_x509_cert(CER_PATH)  # 전체 인증서 (thumbprint 비교용)
PUB_KEY = PUB_CERT.public_key()  # PyJWT 검증에 사용

# --------------------------
# 리다이렉트 안전성
# --------------------------


def is_allowed_redirect(url: str) -> bool:
    """리다이렉트 대상 URL이 허용 목록에 속하는지 검사합니다.

    입력:
    - url: 리다이렉트 대상 URL

    반환:
    - bool: 허용 여부

    부작용:
    - 없음

    오류:
    - 없음(파싱 실패 시 False)
    """

    # -----------------------------------------------------------------------------
    # 1) URL 파싱
    # -----------------------------------------------------------------------------
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    if not parsed.scheme or not parsed.netloc:
        return False

    # -----------------------------------------------------------------------------
    # 2) 허용 스킴 결정
    # -----------------------------------------------------------------------------
    scheme = parsed.scheme.lower()
    allowed_schemes = {"https"}
    # 개발 환경(HTTP 프록시)에서는 http도 허용
    if getattr(settings, "DJANGO_SECURE", True) is False or getattr(settings, "DEBUG", False):
        allowed_schemes.add("http")

    # -----------------------------------------------------------------------------
    # 3) 허용 호스트/스킴 검사
    # -----------------------------------------------------------------------------
    return scheme in allowed_schemes and parsed.netloc in settings.ALLOWED_REDIRECT_HOSTS


# --------------------------
# State 인코딩/디코딩
# --------------------------


def _pad(s: str) -> str:
    """base64url 디코딩을 위해 패딩(=)을 보정합니다.

    입력:
    - s: base64url 문자열

    반환:
    - str: 패딩이 보정된 문자열

    부작용:
    - 없음

    오류:
    - 없음
    """

    # urlsafe_b64decode는 패딩이 없으면 실패할 수 있어 보정
    return s + "=" * (-len(s) % 4)


def b64e(value: str) -> str:
    """문자열을 base64url 문자열로 인코딩합니다.

    입력:
    - value: 원본 문자열

    반환:
    - str: base64url 인코딩 문자열

    부작용:
    - 없음

    오류:
    - 없음
    """

    return base64.urlsafe_b64encode(value.encode("utf-8")).decode("utf-8")


def b64d(value: str) -> str:
    """base64url 문자열을 디코딩해 원본 문자열로 복원합니다.

    입력:
    - value: base64url 문자열

    반환:
    - str: 디코딩된 문자열

    부작용:
    - 없음

    오류:
    - 없음(디코딩 실패 시 상위 예외가 전파됨)
    """

    # 문자열을 반환 (콜백에서 바로 리다이렉트 대상으로 사용 가능)
    return base64.urlsafe_b64decode(_pad(value)).decode("utf-8")


# --------------------------
# 세션 nonce 처리
# --------------------------


def save_nonce(request: HttpRequest, nonce: str) -> None:
    """OIDC nonce 값을 세션에 저장합니다.

    입력:
    - 요청: Django HttpRequest
    - nonce: nonce 문자열

    반환:
    - 없음

    부작용:
    - 세션에 `oidc_nonce` 저장

    오류:
    - 없음
    """

    request.session["oidc_nonce"] = nonce


def pop_nonce(request: HttpRequest) -> str | None:
    """세션에 저장된 OIDC nonce 값을 꺼내고 제거합니다.

    입력:
    - 요청: Django HttpRequest

    반환:
    - str | None: nonce 값 또는 None

    부작용:
    - 세션에서 `oidc_nonce` 제거

    오류:
    - 없음
    """

    return request.session.pop("oidc_nonce", None)


__all__ = [
    "ADFS_AUTH_URL",
    "ADFS_LOGOUT_URL",
    "OIDC_CLIENT_ID",
    "ISSUER",
    "REDIRECT_URI",
    "CER_PATH",
    "PUB_CERT",
    "PUB_KEY",
    "is_allowed_redirect",
    "b64e",
    "b64d",
    "save_nonce",
    "pop_nonce",
    "compute_cert_thumbprint_x5t",
]
