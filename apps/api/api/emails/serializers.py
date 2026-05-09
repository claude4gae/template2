# =============================================================================
# 모듈 설명: Email 응답 직렬화를 담당합니다.
# - 주요 함수: serialize_email_summary, serialize_email_detail
# - 불변 조건: 응답 키는 camelCase를 사용합니다.
# =============================================================================

from __future__ import annotations

from typing import Any, Dict

from django.core.paginator import EmptyPage, Paginator
from rest_framework import serializers

from .models import EmailAsset


def serialize_email_summary(email: Any) -> Dict[str, Any]:
    """Email 인스턴스를 목록 응답용 dict로 직렬화합니다.

    입력:
        email: Email 모델 인스턴스 또는 유사 객체.
    반환:
        목록 응답용 dict (camelCase 키).
    부작용:
        없음.
    오류:
        없음.
    """

    # -----------------------------------------------------------------------------
    # 1) 본문 스니펫 정규화
    # -----------------------------------------------------------------------------
    snippet = (email.body_text or "").strip()
    if len(snippet) > 180:
        snippet = snippet[:177] + "..."

    # -----------------------------------------------------------------------------
    # 2) 응답 payload 구성
    # -----------------------------------------------------------------------------
    return {
        "id": email.id,
        "messageId": email.message_id,
        "receivedAt": email.received_at.isoformat(),
        "subject": email.subject,
        "sender": email.sender,
        "senderId": email.sender_id,
        "recipient": email.recipient,
        "cc": email.cc,
        "userSdwtProd": email.user_sdwt_prod,
        "snippet": snippet,
        "ragDocId": email.rag_doc_id,
        "ragIndexStatus": email.rag_index_status,
    }


def serialize_email_detail(email: Any) -> Dict[str, Any]:
    """Email 인스턴스를 상세 응답용 dict로 직렬화합니다.

    입력:
        email: Email 모델 인스턴스 또는 유사 객체.
    반환:
        상세 응답용 dict (camelCase 키, 본문 포함).
    부작용:
        없음.
    오류:
        없음.
    """

    # -----------------------------------------------------------------------------
    # 1) 상세 응답 구성
    # -----------------------------------------------------------------------------
    return {
        **serialize_email_summary(email),
        "bodyText": email.body_text,
        "createdAt": email.created_at.isoformat(),
        "updatedAt": email.updated_at.isoformat(),
    }


def serialize_email_page(qs: Any, *, page: int, page_size: int) -> Dict[str, Any]:
    """Email 목록 QuerySet을 페이지네이션 응답 dict로 직렬화합니다.

    입력:
        qs: Email QuerySet 또는 iterable.
        page: 요청 페이지 번호.
        page_size: 페이지 크기.
    반환:
        목록/페이지 정보를 포함한 dict.
    부작용:
        QuerySet 평가가 발생할 수 있습니다.
    오류:
        잘못된 페이지 요청은 마지막 페이지로 보정합니다.
    """

    # -----------------------------------------------------------------------------
    # 1) 페이지네이터 구성 및 안전한 페이지 선택
    # -----------------------------------------------------------------------------
    paginator = Paginator(qs, page_size)
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages or 1)

    # -----------------------------------------------------------------------------
    # 2) 기존 API 응답 shape 유지
    # -----------------------------------------------------------------------------
    return {
        "results": [serialize_email_summary(email) for email in page_obj.object_list],
        "page": page_obj.number,
        "pageSize": page_size,
        "total": paginator.count,
        "totalPages": paginator.num_pages,
    }


class EmailAssetOcrClaimSerializer(serializers.Serializer):
    """OCR 작업 클레임 요청을 검증합니다."""

    limit = serializers.IntegerField(min_value=1, required=False)
    lease_seconds = serializers.IntegerField(min_value=1, required=False)
    worker_id = serializers.CharField(required=False, allow_blank=True)


class EmailAssetOcrUpdateItemSerializer(serializers.Serializer):
    """OCR 결과 단일 항목을 검증합니다."""

    asset_id = serializers.IntegerField(min_value=1)
    lock_token = serializers.CharField()
    status = serializers.ChoiceField(choices=[EmailAsset.OcrStatus.DONE, EmailAsset.OcrStatus.FAILED])
    text = serializers.CharField(required=False, allow_blank=True)
    error_code = serializers.CharField(required=False, allow_blank=True)
    error_message = serializers.CharField(required=False, allow_blank=True)
    ocr_model = serializers.CharField(required=False, allow_blank=True)
    ocr_duration_ms = serializers.IntegerField(min_value=0, required=False)
    processed_at = serializers.DateTimeField(required=False)


class EmailAssetOcrUpdateSerializer(serializers.Serializer):
    """OCR 결과 업데이트 요청을 검증합니다."""

    results = EmailAssetOcrUpdateItemSerializer(many=True)


__all__ = [
    "EmailAssetOcrClaimSerializer",
    "EmailAssetOcrUpdateSerializer",
    "EmailAssetOcrUpdateItemSerializer",
    "serialize_email_detail",
    "serialize_email_page",
    "serialize_email_summary",
]
