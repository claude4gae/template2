# =============================================================================
# 모듈 설명: RAG 설정 로드/정규화 헬퍼를 제공합니다.
# - 주요 대상: RAG_* 설정값, _normalize_permission_groups, _normalize_index_names
# - 불변 조건: env 또는 Django settings에서 설정을 읽어옵니다.
# =============================================================================

"""RAG 설정 값을 읽고 정규화하는 헬퍼 모음.

- 주요 대상: RAG_* 설정값, 헤더/그룹/인덱스 정규화 함수
- 주요 엔드포인트/클래스: 없음(설정 상수 및 함수 제공)
- 가정/불변 조건: 설정값은 env 또는 Django settings에서 제공됨
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Sequence

from django.conf import settings


def _read_setting(name: str, default: str | None = None) -> str | None:
    """환경변수/설정에서 값을 읽어 문자열로 반환합니다.

    입력:
    - name: 설정 키 이름
    - default: 기본값

    반환:
    - str | None: 설정 문자열 또는 None

    부작용:
    - 없음

    오류:
    - 없음
    """

    # -----------------------------------------------------------------------------
    # 1) 환경변수 우선 조회
    # -----------------------------------------------------------------------------
    value = os.environ.get(name)
    if value is None:
        # -----------------------------------------------------------------------------
        # 2) Django settings 폴백
        # -----------------------------------------------------------------------------
        value = getattr(settings, name, default)
    if value is None:
        return None
    if isinstance(value, str):
        return value
    # -----------------------------------------------------------------------------
    # 3) 문자열 변환
    # -----------------------------------------------------------------------------
    return str(value)


def _parse_headers(raw: str | None) -> Dict[str, str]:
    """JSON 문자열 헤더 설정을 dict[str, str]로 파싱합니다.

    입력:
    - raw: JSON 문자열

    반환:
    - Dict[str, str]: 헤더 딕셔너리

    부작용:
    - 없음

    오류:
    - 없음(파싱 실패 시 빈 dict 반환)
    """

    # -----------------------------------------------------------------------------
    # 1) 입력 유효성 확인
    # -----------------------------------------------------------------------------
    if not raw:
        return {}
    # -----------------------------------------------------------------------------
    # 2) JSON 파싱
    # -----------------------------------------------------------------------------
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}
    if not isinstance(parsed, dict):
        return {}

    # -----------------------------------------------------------------------------
    # 3) 문자열 헤더만 정규화
    # -----------------------------------------------------------------------------
    headers: Dict[str, str] = {}
    for key, value in parsed.items():
        if isinstance(key, str) and isinstance(value, (str, int, float, bool)):
            headers[key] = str(value)
    return headers


def _parse_permission_groups(raw: str | None) -> List[str]:
    """권한 그룹 설정(JSON 배열 또는 CSV)을 문자열 리스트로 정규화합니다.

    입력:
    - raw: JSON 배열 문자열 또는 CSV 문자열

    반환:
    - List[str]: 권한 그룹 목록

    부작용:
    - 없음

    오류:
    - 없음(파싱 실패 시 빈 리스트 반환)
    """

    # -----------------------------------------------------------------------------
    # 1) 입력 유효성 확인
    # -----------------------------------------------------------------------------
    if not raw:
        return []
    # -----------------------------------------------------------------------------
    # 2) JSON 파싱 시도
    # -----------------------------------------------------------------------------
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        parsed = None

    # -----------------------------------------------------------------------------
    # 3) JSON 배열 처리
    # -----------------------------------------------------------------------------
    if isinstance(parsed, Sequence) and not isinstance(parsed, (str, bytes, bytearray)):
        return [str(item).strip() for item in parsed if str(item).strip()]

    # -----------------------------------------------------------------------------
    # 4) CSV 문자열 처리
    # -----------------------------------------------------------------------------
    if isinstance(raw, str):
        return [item.strip() for item in raw.split(",") if item.strip()]

    # -----------------------------------------------------------------------------
    # 5) 기본값 반환
    # -----------------------------------------------------------------------------
    return []


def _parse_index_list(raw: str | None) -> List[str]:
    """인덱스 목록 설정(JSON 배열 또는 CSV)을 문자열 리스트로 정규화합니다.

    입력:
    - raw: JSON 배열 문자열 또는 CSV 문자열

    반환:
    - List[str]: 인덱스 이름 목록

    부작용:
    - 없음

    오류:
    - 없음
    """

    return _parse_permission_groups(raw)


def _parse_chunk_factor(raw: str | None) -> Dict[str, str | int] | None:
    """chunk_factor 설정(JSON 객체)을 정규화해 dict로 반환합니다.

    입력:
    - raw: JSON 객체 문자열

    반환:
    - Dict[str, str | int] | None: 정규화된 chunk_factor

    부작용:
    - 없음

    오류:
    - 없음(파싱 실패 시 None)
    """

    # -----------------------------------------------------------------------------
    # 1) 입력 유효성 확인
    # -----------------------------------------------------------------------------
    if not raw:
        return None
    # -----------------------------------------------------------------------------
    # 2) JSON 파싱
    # -----------------------------------------------------------------------------
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(parsed, dict):
        return None
    # -----------------------------------------------------------------------------
    # 3) 허용 타입만 정규화
    # -----------------------------------------------------------------------------
    normalized: Dict[str, str | int] = {}
    for key, value in parsed.items():
        if not isinstance(key, str):
            continue
        if isinstance(value, (str, int)):
            normalized[key] = value
    return normalized or None


def _normalize_string_sequence(
    values: Sequence[str] | str | None,
    *,
    split_commas: bool = False,
    dedupe: bool = False,
) -> List[str]:
    """문자열/시퀀스 입력을 공통 규칙으로 정규화합니다.

    입력:
    - values: 문자열 또는 문자열 시퀀스
    - split_commas: 문자열 입력을 CSV로 분리할지 여부
    - dedupe: 중복 제거 여부

    반환:
    - List[str]: 공백 제거가 끝난 문자열 목록

    부작용:
    - 없음

    오류:
    - 없음
    """

    # -----------------------------------------------------------------------------
    # 1) 입력 유효성 확인 및 리스트화
    # -----------------------------------------------------------------------------
    if not values:
        return []
    if isinstance(values, str):
        raw_values = values.split(",") if split_commas else [values]
    elif isinstance(values, Sequence):
        raw_values = list(values)
    else:
        return []

    # -----------------------------------------------------------------------------
    # 2) 값 정제
    # -----------------------------------------------------------------------------
    normalized: List[str] = []
    for value in raw_values:
        if value is None:
            continue
        cleaned = str(value).strip()
        if cleaned:
            normalized.append(cleaned)
    if dedupe:
        return list(dict.fromkeys(normalized))
    return normalized


def _normalize_permission_groups(groups: Sequence[str] | str | None) -> List[str]:
    """permission_groups 입력을 문자열 리스트로 정규화합니다.

    입력:
    - groups: 문자열 또는 문자열 시퀀스

    반환:
    - List[str]: 정규화된 권한 그룹 목록

    부작용:
    - 없음

    오류:
    - 없음
    """

    return _normalize_string_sequence(groups)


def _normalize_index_names(index_names: Sequence[str] | str | None) -> List[str]:
    """index_name 입력을 문자열 리스트로 정규화합니다.

    입력:
    - index_names: 문자열 또는 문자열 시퀀스

    반환:
    - List[str]: 중복 제거된 인덱스 이름 목록

    부작용:
    - 없음

    오류:
    - 없음
    """

    return _normalize_string_sequence(index_names, split_commas=True, dedupe=True)


# =============================================================================
# 설정값 로드 및 정규화
# =============================================================================


RAG_SEARCH_URL = _read_setting("ASSISTANT_RAG_URL") or _read_setting("RAG_SEARCH_URL", "")
RAG_INSERT_URL = _read_setting("ASSISTANT_RAG_INSERT_URL") or _read_setting("RAG_INSERT_URL", "")
RAG_DELETE_URL = _read_setting("ASSISTANT_RAG_DELETE_URL") or _read_setting("RAG_DELETE_URL", "")
RAG_INDEX_NAME = _read_setting("ASSISTANT_RAG_INDEX_NAME") or _read_setting("RAG_INDEX_NAME", "")
RAG_INDEX_DEFAULT = (
    _read_setting("ASSISTANT_RAG_INDEX_DEFAULT")
    or _read_setting("RAG_INDEX_DEFAULT")
    or RAG_INDEX_NAME
    or ""
)
RAG_INDEX_EMAILS = (
    _read_setting("ASSISTANT_RAG_INDEX_EMAILS")
    or _read_setting("RAG_INDEX_EMAILS")
    or ""
)
RAG_INDEX_LIST = _parse_index_list(
    _read_setting("ASSISTANT_RAG_INDEX_LIST") or _read_setting("RAG_INDEX_LIST")
)
RAG_PERMISSION_GROUPS = (
    _parse_permission_groups(_read_setting("ASSISTANT_RAG_PERMISSION_GROUPS"))
    or _parse_permission_groups(_read_setting("RAG_PERMISSION_GROUPS"))
)
RAG_PUBLIC_GROUP = "rag-public"
RAG_CHUNK_FACTOR = _parse_chunk_factor(
    _read_setting("ASSISTANT_RAG_CHUNK_FACTOR") or _read_setting("RAG_CHUNK_FACTOR")
)
RAG_ERROR_LOG_PATH = _read_setting("RAG_ERROR_LOG_PATH") or str(Path(settings.BASE_DIR) / "logs" / "rag_errors.log")

# -----------------------------------------------------------------------------
# 헤더 구성
# -----------------------------------------------------------------------------
_custom_headers = _parse_headers(_read_setting("ASSISTANT_RAG_HEADERS")) or _parse_headers(_read_setting("RAG_HEADERS"))
if _custom_headers:
    RAG_HEADERS = {"Content-Type": "application/json", **_custom_headers}
else:
    RAG_HEADERS = {
        "Content-Type": "application/json",
        "x-dep-ticket": _read_setting("RAG_PASS_KEY", "") or "",
        "api-key": _read_setting("RAG_API_KEY", "") or "",
    }

# -----------------------------------------------------------------------------
# 권한 그룹 기본값 보정
# -----------------------------------------------------------------------------
if not RAG_PERMISSION_GROUPS:
    RAG_PERMISSION_GROUPS = [RAG_PUBLIC_GROUP]

# -----------------------------------------------------------------------------
# 인덱스 목록 정규화
# -----------------------------------------------------------------------------
_resolved_index_list: List[str] = []
for value in [*RAG_INDEX_LIST, RAG_INDEX_DEFAULT, RAG_INDEX_EMAILS]:
    cleaned = str(value).strip() if isinstance(value, str) else ""
    if cleaned and cleaned not in _resolved_index_list:
        _resolved_index_list.append(cleaned)
RAG_INDEX_LIST = _resolved_index_list

__all__ = [
    "RAG_CHUNK_FACTOR",
    "RAG_DELETE_URL",
    "RAG_HEADERS",
    "RAG_INDEX_DEFAULT",
    "RAG_INDEX_EMAILS",
    "RAG_INDEX_LIST",
    "RAG_INDEX_NAME",
    "RAG_INSERT_URL",
    "RAG_PUBLIC_GROUP",
    "RAG_PERMISSION_GROUPS",
    "RAG_SEARCH_URL",
    "_normalize_index_names",
    "_normalize_permission_groups",
]
