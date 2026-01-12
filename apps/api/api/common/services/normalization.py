# 공용 정규화 유틸

"""데이터 정규화 및 검증 함수 모음."""
from __future__ import annotations

from typing import Any, Optional

from .constants import DATE_ONLY_REGEX, SAFE_IDENTIFIER


def _sanitize_identifier_value(value: Any) -> Optional[str]:
    """식별자 후보 문자열을 안전한 정규식으로 검증합니다.

    입력:
    - value: 식별자 후보 값

    반환:
    - Optional[str]: 정규화된 식별자 또는 None

    부작용:
    - 없음

    오류:
    - 없음
    """

    # -----------------------------------------------------------------------------
    # 1) 타입/공백 정리
    # -----------------------------------------------------------------------------
    if not isinstance(value, str):
        return None
    candidate = value.strip()

    # -----------------------------------------------------------------------------
    # 2) 정규식 검증
    # -----------------------------------------------------------------------------
    return candidate if SAFE_IDENTIFIER.match(candidate) else None


def sanitize_identifier(value: Any, fallback: Optional[str] = None) -> Optional[str]:
    """식별자 문자열을 안전한 정규식으로 검증합니다.

    입력:
    - value: 원본 식별자 후보 값
    - fallback: 검증 실패 시 사용할 기본값

    반환:
    - Optional[str]: 유효한 식별자 문자열 또는 None

    부작용:
    - 없음

    오류:
    - 없음
    """

    # -----------------------------------------------------------------------------
    # 1) 기본 값 검증
    # -----------------------------------------------------------------------------
    normalized = _sanitize_identifier_value(value)
    if normalized:
        return normalized

    # -----------------------------------------------------------------------------
    # 2) fallback 검증
    # -----------------------------------------------------------------------------
    return _sanitize_identifier_value(fallback)


def normalize_date_only(value: Any) -> Optional[str]:
    """YYYY-MM-DD 형식 문자열만 허용합니다."""
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    return candidate if DATE_ONLY_REGEX.match(candidate) else None


def normalize_line_id(value: Any) -> Optional[str]:
    """lineId 쿼리 파라미터를 정규화합니다."""
    if not isinstance(value, str):
        return None
    trimmed = value.strip()
    return trimmed or None


def normalize_text(value: Any) -> str:
    """텍스트 필드를 트림하고 비문자열은 빈 문자열로 처리합니다."""
    if not isinstance(value, str):
        return ""
    return value.strip()


def to_int(value: Any) -> int:
    """값을 정수로 변환하고 실패 시 0을 반환합니다."""
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0

__all__ = [
    "sanitize_identifier",
    "normalize_date_only",
    "normalize_line_id",
    "normalize_text",
    "to_int",
]
