# =============================================================================
# 모듈: Drone SOP POP3 공통 유틸
# 주요 기능: URL 문자열 정규화
# 주요 가정: POP3 수집/사이드카 모듈이 함께 재사용합니다.
# =============================================================================
"""Drone SOP POP3 공통 유틸리티 모듈입니다."""

from __future__ import annotations

from typing import Any


def sanitize_url(value: Any) -> str | None:
    """URL 문자열을 정리하고 비어 있으면 None을 반환합니다.

    인자:
        value: 원본 URL 값.

    반환:
        정리된 URL 문자열 또는 None.

    부작용:
        없음. 순수 정규화입니다.
    """

    if value is None:
        return None
    cleaned = str(value).replace('"', "").strip()
    return cleaned or None


__all__ = ["sanitize_url"]
