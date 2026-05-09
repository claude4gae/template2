# =============================================================================
# 모듈: 어시스턴트 출처/segment 매핑
# 주요 함수: filter_sources_by_used_email_ids, build_structured_segments
# 주요 가정: LLM이 반환한 emailId가 RAG 출처에 있을 때만 화면 출처로 노출합니다.
# =============================================================================
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .reply import AssistantStructuredSegment


def filter_sources_by_used_email_ids(
    sources: List[Dict[str, Any]],
    used_email_ids: List[str],
) -> List[Dict[str, Any]]:
    """출처 목록에서 사용된 emailId(doc_id)만 남깁니다.

    인자:
        sources: 원본 출처 목록.
        used_email_ids: 사용된 emailId 목록.

    반환:
        used_email_ids에 포함된 doc_id만 남긴 출처 목록.

    부작용:
        없음. 순수 필터링입니다.
    """

    if not used_email_ids:
        return []

    allowed_ids = {
        entry.get("doc_id").strip()
        for entry in sources
        if isinstance(entry, dict)
        and isinstance(entry.get("doc_id"), str)
        and entry.get("doc_id").strip()
    }
    used_set = {email_id for email_id in used_email_ids if email_id in allowed_ids}
    if not used_set:
        return []

    return [
        entry
        for entry in sources
        if isinstance(entry, dict)
        and isinstance(entry.get("doc_id"), str)
        and entry.get("doc_id").strip() in used_set
    ]


def build_structured_segments(
    sources: List[Dict[str, Any]],
    segments: List[AssistantStructuredSegment],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """LLM segment 목록을 기반으로 segment별 출처와 전체 출처를 계산합니다.

    인자:
        sources: 원본 출처 목록.
        segments: LLM 구조화 응답의 segment 목록.

    반환:
        (segments, sources) 튜플.
        - segments: [{"reply": str, "sources": list[dict]}] (세그먼트별 응답/출처)
        - sources: 전체 segment에서 사용된 출처(중복 제거)

    부작용:
        없음. 순수 계산입니다.
    """

    allowed_ids = {
        entry.get("doc_id").strip()
        for entry in sources
        if isinstance(entry, dict)
        and isinstance(entry.get("doc_id"), str)
        and entry.get("doc_id").strip()
    }

    normalized_segments: List[Dict[str, Any]] = []
    used_ids_union: List[str] = []

    for segment in segments:
        used_ids = [email_id for email_id in segment.used_email_ids if email_id in allowed_ids]
        if not used_ids:
            continue

        segment_sources = filter_sources_by_used_email_ids(sources, used_ids)
        if not segment_sources:
            continue

        normalized_segments.append(
            {
                "reply": segment.answer,
                "sources": segment_sources,
            }
        )

        for email_id in used_ids:
            if email_id not in used_ids_union:
                used_ids_union.append(email_id)

    filtered_sources = filter_sources_by_used_email_ids(sources, used_ids_union)
    return normalized_segments, filtered_sources
