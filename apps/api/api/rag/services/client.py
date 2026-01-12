# =============================================================================
# 모듈 설명: RAG API 클라이언트 동작을 담당합니다.
# - 주요 대상: search_rag, insert_email_to_rag, delete_rag_doc
# - 불변 조건: RAG 설정값은 api.rag.services.config에서 제공합니다.
# =============================================================================

"""RAG API 클라이언트 동작을 담당하는 모듈.

- 주요 대상: search_rag, insert_email_to_rag, delete_rag_doc
- 주요 엔드포인트/클래스: 없음(서비스 함수 제공)
- 가정/불변 조건: RAG 설정 값은 api.rag.services.config에서 제공됨
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Sequence

import requests
from django.utils import timezone

from .config import _normalize_index_names, _normalize_permission_groups
from .logging import _log_rag_failure


def _get_rag_services():
    """RAG 설정 모듈을 지연 로드해 반환합니다.

    입력:
    - 없음

    반환:
    - module: api.rag.services 모듈

    부작용:
    - 모듈 로드

    오류:
    - ImportError: 모듈 로드 실패 시
    """
    from api.rag import services as rag_services

    return rag_services


def _resolve_email_permission_groups(email: Any) -> List[str]:
    """이메일 속성을 permission_groups로 변환합니다.

    입력:
    - email: 이메일 객체

    반환:
    - List[str]: 권한 그룹 목록

    부작용:
    - 없음

    오류:
    - 없음
    """

    # -----------------------------------------------------------------------------
    # 1) 이메일 속성 기반 그룹 수집
    # -----------------------------------------------------------------------------
    rag_services = _get_rag_services()
    groups: List[str] = []
    raw_group = getattr(email, "user_sdwt_prod", None)
    if isinstance(raw_group, str) and raw_group.strip():
        groups.append(raw_group.strip())
    raw_sender_id = getattr(email, "sender_id", None)
    if isinstance(raw_sender_id, str) and raw_sender_id.strip():
        groups.append(raw_sender_id.strip())
    # -----------------------------------------------------------------------------
    # 2) 중복 제거 및 기본값 폴백
    # -----------------------------------------------------------------------------
    if groups:
        return list(dict.fromkeys(groups))
    return _normalize_permission_groups(rag_services.RAG_PERMISSION_GROUPS) or [rag_services.RAG_PUBLIC_GROUP]


def get_rag_index_candidates() -> List[str]:
    """허용 가능한 RAG 인덱스 후보 목록을 반환합니다.

    입력:
    - 없음

    반환:
    - List[str]: 인덱스 이름 목록

    부작용:
    - 없음

    오류:
    - 없음
    """

    rag_services = _get_rag_services()
    return list(rag_services.RAG_INDEX_LIST)


def resolve_rag_index_name(index_name: str | None) -> str:
    """RAG 인덱스명을 결정합니다.

    입력:
    - index_name: 요청된 인덱스명

    반환:
    - str: 최종 인덱스명(없으면 빈 문자열)

    부작용:
    - 없음

    오류:
    - 없음
    """

    # -----------------------------------------------------------------------------
    # 1) 요청 값 우선 사용
    # -----------------------------------------------------------------------------
    rag_services = _get_rag_services()
    resolved = index_name.strip() if isinstance(index_name, str) else ""
    if resolved:
        return resolved

    # -----------------------------------------------------------------------------
    # 2) 기본값 폴백
    # -----------------------------------------------------------------------------
    default_index = str(rag_services.RAG_INDEX_DEFAULT or "").strip()
    if default_index:
        return default_index
    if rag_services.RAG_INDEX_LIST:
        return rag_services.RAG_INDEX_LIST[0]
    return ""


def resolve_rag_index_names(index_names: Sequence[str] | str | None) -> List[str]:
    """RAG 인덱스 목록을 정규화하고 기본값을 보정합니다.

    입력:
    - index_names: 인덱스명 또는 인덱스명 시퀀스

    반환:
    - List[str]: 정규화된 인덱스 목록

    부작용:
    - 없음

    오류:
    - 없음
    """

    # -----------------------------------------------------------------------------
    # 1) 입력값 정규화
    # -----------------------------------------------------------------------------
    resolved = _normalize_index_names(index_names)
    if resolved:
        return resolved
    # -----------------------------------------------------------------------------
    # 2) 단일 기본값 폴백
    # -----------------------------------------------------------------------------
    fallback = resolve_rag_index_name(None)
    return [fallback] if fallback else []


def _build_insert_payload(
    email: Any,
    index_name: str | None = None,
    permission_groups: Sequence[str] | None = None,
) -> Dict[str, Any]:
    """이메일 객체를 RAG insert 요청 payload로 변환합니다.

    입력:
    - email: 이메일 객체
    - index_name: 인덱스명(선택)
    - permission_groups: 권한 그룹(선택)

    반환:
    - Dict[str, Any]: RAG insert payload(삽입 요청 본문)

    부작용:
    - 없음

    오류:
    - 없음
    """

    # -----------------------------------------------------------------------------
    # 1) 인덱스/시간/수신자 정규화
    # -----------------------------------------------------------------------------
    rag_services = _get_rag_services()
    resolved_index_name = resolve_rag_index_name(index_name)
    created_time = getattr(email, "received_at", None) or timezone.now()
    recipient_value = getattr(email, "recipient", None)
    if isinstance(recipient_value, (list, tuple)):
        recipient = ", ".join([str(item).strip() for item in recipient_value if str(item).strip()])
    else:
        recipient = recipient_value
    # -----------------------------------------------------------------------------
    # 2) 권한 그룹 정규화
    # -----------------------------------------------------------------------------
    resolved_permission_groups = (
        _normalize_permission_groups(permission_groups)
        if permission_groups is not None
        else _normalize_permission_groups(rag_services.RAG_PERMISSION_GROUPS)
    )
    # -----------------------------------------------------------------------------
    # 3) 페이로드 구성
    # -----------------------------------------------------------------------------
    payload: Dict[str, Any] = {
        "index_name": resolved_index_name,
        "data": {
            "doc_id": getattr(email, "rag_doc_id", None),
            "title": email.subject,
            "content": email.body_text or "",
            "permission_groups": resolved_permission_groups,
            "created_time": created_time.isoformat(),
            "department": getattr(email, "department", None),
            "line": getattr(email, "line", None),
            "user_sdwt_prod": getattr(email, "user_sdwt_prod", None),
            "email_id": email.id,
            "sender": email.sender,
            "recipient": recipient,
            "received_at": created_time.isoformat(),
        },
    }
    # -----------------------------------------------------------------------------
    # 4) chunk_factor 옵션 반영
    # -----------------------------------------------------------------------------
    if rag_services.RAG_CHUNK_FACTOR:
        payload["chunk_factor"] = rag_services.RAG_CHUNK_FACTOR
    return payload


def _build_delete_payload(
    doc_id: str,
    index_name: str | None = None,
    permission_groups: Sequence[str] | None = None,
) -> Dict[str, Any]:
    """doc_id 기반 RAG delete 요청 payload를 생성합니다.

    입력:
    - doc_id: 문서 식별자
    - index_name: 인덱스명(선택)
    - permission_groups: 권한 그룹(선택)

    반환:
    - Dict[str, Any]: RAG delete payload(삭제 요청 본문)

    부작용:
    - 없음

    오류:
    - 없음
    """

    # -----------------------------------------------------------------------------
    # 1) 인덱스/권한 그룹 정규화
    # -----------------------------------------------------------------------------
    rag_services = _get_rag_services()
    resolved_index_name = resolve_rag_index_name(index_name)
    resolved_permission_groups = (
        _normalize_permission_groups(permission_groups)
        if permission_groups is not None
        else _normalize_permission_groups(rag_services.RAG_PERMISSION_GROUPS)
    )
    # -----------------------------------------------------------------------------
    # 2) 페이로드 구성
    # -----------------------------------------------------------------------------
    return {
        "index_name": resolved_index_name,
        "permission_groups": resolved_permission_groups,
        "doc_id": doc_id,
    }


def _build_search_payload(
    query_text: str,
    *,
    index_name: Sequence[str] | str | None = None,
    num_result_doc: int = 5,
    permission_groups: Sequence[str] | None = None,
) -> Dict[str, Any]:
    """RAG search 요청 payload를 생성합니다.

    입력:
    - query_text: 검색 질의문
    - index_name: 인덱스명 또는 인덱스명 시퀀스
    - num_result_doc: 반환 문서 개수
    - permission_groups: 권한 그룹(선택)

    반환:
    - Dict[str, Any]: RAG search payload(검색 요청 본문)

    부작용:
    - 없음

    오류:
    - 없음
    """

    # -----------------------------------------------------------------------------
    # 1) 인덱스명 정규화
    # -----------------------------------------------------------------------------
    rag_services = _get_rag_services()
    resolved_index_names = resolve_rag_index_names(index_name)
    resolved_index_name = ",".join(resolved_index_names)

    # -----------------------------------------------------------------------------
    # 2) 질의/개수 정규화
    # -----------------------------------------------------------------------------
    if query_text is None:
        normalized_query = ""
    else:
        normalized_query = str(query_text).strip()
    normalized_num = int(num_result_doc) if isinstance(num_result_doc, int) else 5
    if normalized_num <= 0:
        normalized_num = 5

    # -----------------------------------------------------------------------------
    # 3) 페이로드 구성
    # -----------------------------------------------------------------------------
    return {
        "index_name": resolved_index_name,
        "permission_groups": _normalize_permission_groups(permission_groups)
        if permission_groups is not None
        else _normalize_permission_groups(rag_services.RAG_PERMISSION_GROUPS),
        "query_text": normalized_query,
        "num_result_doc": normalized_num,
    }


def search_rag(
    query_text: str,
    *,
    index_name: Sequence[str] | str | None = None,
    num_result_doc: int = 5,
    permission_groups: Sequence[str] | None = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    """RAG에서 query_text 기반으로 문서를 검색합니다.

    입력:
    - query_text: 검색 질의문
    - index_name: 인덱스명 또는 인덱스명 시퀀스
    - num_result_doc: 반환 문서 개수
    - permission_groups: 권한 그룹(선택)
    - timeout: HTTP 타임아웃(초)

    반환:
    - Dict[str, Any]: RAG 서버 JSON 응답

    부작용:
    - RAG 서버로 HTTP 요청 수행

    오류:
    - ValueError: 필수 설정 누락 또는 입력값 오류
    - requests.RequestException: 네트워크/HTTP 오류
    - json.JSONDecodeError: JSON 파싱 실패
    """

    # -----------------------------------------------------------------------------
    # 1) 요청 페이로드 구성
    # -----------------------------------------------------------------------------
    payload = _build_search_payload(
        query_text,
        index_name=index_name,
        num_result_doc=num_result_doc,
        permission_groups=permission_groups,
    )

    resolved_index_name = payload.get("index_name")

    # -----------------------------------------------------------------------------
    # 2) 필수 설정 및 입력 검증
    # -----------------------------------------------------------------------------
    rag_services = _get_rag_services()
    if not rag_services.RAG_SEARCH_URL:
        error = ValueError("RAG_SEARCH_URL is not configured")
        _log_rag_failure("search", payload, error)
        raise error
    if not resolved_index_name:
        error = ValueError("RAG_INDEX_DEFAULT is not configured")
        _log_rag_failure("search", payload, error)
        raise error
    if not payload.get("query_text"):
        error = ValueError("query_text is empty")
        _log_rag_failure("search", payload, error)
        raise error

    # -----------------------------------------------------------------------------
    # 3) HTTP 요청 및 응답 처리
    # -----------------------------------------------------------------------------
    try:
        resp = requests.post(
            rag_services.RAG_SEARCH_URL,
            headers=rag_services.RAG_HEADERS,
            json=payload,
            timeout=max(1, int(timeout)),
        )
        resp.raise_for_status()
        try:
            return resp.json()
        except (json.JSONDecodeError, ValueError) as exc:
            _log_rag_failure("search", payload, exc, response=resp)
            raise
    # -----------------------------------------------------------------------------
    # 4) 오류 로깅 및 재전파
    # -----------------------------------------------------------------------------
    except Exception as exc:
        _log_rag_failure("search", payload, exc)
        raise


def insert_email_to_rag(
    email: Any,
    index_name: str | None = None,
    permission_groups: Sequence[str] | None = None,
) -> None:
    """Email 모델을 RAG 인덱스에 등록합니다.

    입력:
    - email: 이메일 객체
    - index_name: 인덱스명(선택)
    - permission_groups: 권한 그룹(선택)

    반환:
    - 없음

    부작용:
    - RAG 서버로 HTTP 요청 수행

    오류:
    - ValueError: 필수 설정 누락
    - requests.RequestException: 네트워크/HTTP 오류
    """

    # -----------------------------------------------------------------------------
    # 1) 권한 그룹/페이로드 구성
    # -----------------------------------------------------------------------------
    rag_services = _get_rag_services()
    resolved_permission_groups = (
        _resolve_email_permission_groups(email)
        if permission_groups is None
        else _normalize_permission_groups(permission_groups)
    )
    payload = _build_insert_payload(
        email,
        index_name=index_name,
        permission_groups=resolved_permission_groups,
    )

    resolved_index_name = payload.get("index_name")

    # -----------------------------------------------------------------------------
    # 2) 필수 설정 검증
    # -----------------------------------------------------------------------------
    if not rag_services.RAG_INSERT_URL:
        error = ValueError("RAG_INSERT_URL is not configured")
        _log_rag_failure("insert", payload, error)
        raise error
    if not resolved_index_name:
        error = ValueError("RAG_INDEX_DEFAULT is not configured")
        _log_rag_failure("insert", payload, error)
        raise error

    # -----------------------------------------------------------------------------
    # 3) HTTP 요청 수행
    # -----------------------------------------------------------------------------
    try:
        resp = requests.post(
            rag_services.RAG_INSERT_URL,
            headers=rag_services.RAG_HEADERS,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
    except Exception as exc:
        _log_rag_failure("insert", payload, exc)
        raise


def delete_rag_doc(
    doc_id: str,
    index_name: str | None = None,
    permission_groups: Sequence[str] | None = None,
) -> None:
    """RAG에서 doc_id에 해당하는 문서를 삭제합니다.

    입력:
    - doc_id: 문서 식별자
    - index_name: 인덱스명(선택)
    - permission_groups: 권한 그룹(선택)

    반환:
    - 없음

    부작용:
    - RAG 서버로 HTTP 요청 수행

    오류:
    - ValueError: 필수 설정 누락
    - requests.RequestException: 네트워크/HTTP 오류
    """

    # -----------------------------------------------------------------------------
    # 1) 페이로드 구성
    # -----------------------------------------------------------------------------
    rag_services = _get_rag_services()
    payload = _build_delete_payload(doc_id, index_name=index_name, permission_groups=permission_groups)

    resolved_index_name = payload.get("index_name")

    # -----------------------------------------------------------------------------
    # 2) 필수 설정 검증
    # -----------------------------------------------------------------------------
    if not rag_services.RAG_DELETE_URL:
        error = ValueError("RAG_DELETE_URL is not configured")
        _log_rag_failure("delete", payload, error)
        raise error
    if not resolved_index_name:
        error = ValueError("RAG_INDEX_DEFAULT is not configured")
        _log_rag_failure("delete", payload, error)
        raise error

    # -----------------------------------------------------------------------------
    # 3) HTTP 요청 수행
    # -----------------------------------------------------------------------------
    try:
        resp = requests.post(
            rag_services.RAG_DELETE_URL,
            headers=rag_services.RAG_HEADERS,
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
    except Exception as exc:
        _log_rag_failure("delete", payload, exc)
        raise
