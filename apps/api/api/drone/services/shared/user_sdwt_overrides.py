# =============================================================================
# 모듈: Drone SOP user_sdwt_prod override 설정
# 주요 기능: 환경변수 기반 comment keyword -> user_sdwt_prod 매핑 관리
# 주요 가정: parser와 Engr 후보 API가 같은 환경변수를 사용합니다.
# =============================================================================
"""Drone SOP user_sdwt_prod override 설정 유틸리티입니다."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from typing import Any

def _normalize_text(value: Any) -> str:
    """환경변수 입력값을 공백 제거 문자열로 정규화합니다."""

    return str(value or "").strip()


def _normalize_mapping(payload: Mapping[Any, Any]) -> dict[str, str]:
    """JSON mapping payload에서 유효한 문자열 매핑만 추출합니다."""

    normalized: dict[str, str] = {}
    for raw_key, raw_value in payload.items():
        key = _normalize_text(raw_key)
        value = _normalize_text(raw_value)
        if key and value:
            normalized[key] = value
    return normalized


def get_comment_user_sdwt_override_map() -> dict[str, str]:
    """환경변수 기준 comment keyword override map을 반환합니다."""

    raw_value = os.getenv("DRONE_SOP_USER_SDWT_OVERRIDE_MAP", "").strip()
    if not raw_value:
        return {}
    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, Mapping):
        return {}
    normalized = _normalize_mapping(parsed)
    return normalized


def resolve_comment_user_sdwt_override(comment: Any) -> str | None:
    """comment 문구에서 override map에 해당하는 user_sdwt_prod 값을 찾습니다."""

    normalized_comment = str(comment or "").strip().casefold()
    for keyword, fallback in get_comment_user_sdwt_override_map().items():
        if keyword.casefold() in normalized_comment:
            return fallback
    return None


def list_engr_mapping_values_from_env() -> list[str]:
    """Engr 지정 조합 드롭다운에 추가할 fallback 및 override 값을 반환합니다."""

    raw_fallbacks = os.getenv("DRONE_SOP_ENGR_FALLBACK_VALUES", "").strip()
    fallback_values = raw_fallbacks.split(",") if raw_fallbacks else []
    values = [
        *(_normalize_text(value) for value in fallback_values),
        *get_comment_user_sdwt_override_map().values(),
    ]
    display_by_key: dict[str, str] = {}
    for value in values:
        normalized = _normalize_text(value)
        if normalized:
            display_by_key.setdefault(normalized.casefold(), normalized)
    return sorted(display_by_key.values())


__all__ = [
    "get_comment_user_sdwt_override_map",
    "list_engr_mapping_values_from_env",
    "resolve_comment_user_sdwt_override",
]
