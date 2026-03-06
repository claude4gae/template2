# 공용 정규화 유틸

"""도메인 공통 텍스트 정규화 함수 모음."""
from __future__ import annotations

from typing import Any


def normalize_text(value: Any) -> str:
    """텍스트 필드를 트림하고 비문자열은 빈 문자열로 처리합니다."""

    if not isinstance(value, str):
        return ""
    return value.strip()


__all__ = ["normalize_text"]
