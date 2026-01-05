# =============================================================================
# 모듈 설명: 이메일 이미지 OCR 작업 클레임/결과 반영 및 RAG 재인덱싱 요청을 처리합니다.
# - 주요 함수: claim_email_asset_ocr_tasks, update_email_asset_ocr_results
# - 불변 조건: OCR 상태는 PENDING/PROCESSING/DONE/FAILED 흐름을 따릅니다.
# =============================================================================

from __future__ import annotations

import logging
import secrets
from datetime import timedelta
from typing import Any, Dict, Sequence

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from api.common.services import UNASSIGNED_USER_SDWT_PROD

from ..models import Email, EmailAsset
from ..selectors import (
    get_email_asset_by_id,
    get_email_by_id,
    has_unprocessed_email_assets,
    list_claimable_email_assets_for_update,
)
from .rag import enqueue_rag_index

# =============================================================================
# 로깅
# =============================================================================
logger = logging.getLogger(__name__)


def _should_enqueue_rag(*, email: Email) -> bool:
    """OCR 완료 후 RAG 재인덱싱 대상 여부를 판단합니다.

    입력:
        email: Email 인스턴스.
    반환:
        RAG 재인덱싱 대상이면 True.
    부작용:
        없음.
    오류:
        없음.
    """

    # -----------------------------------------------------------------------------
    # 1) 분류 출처 확인
    # -----------------------------------------------------------------------------
    if email.classification_source != Email.ClassificationSource.CONFIRMED_USER:
        return False

    # -----------------------------------------------------------------------------
    # 2) user_sdwt_prod 유효성 확인
    # -----------------------------------------------------------------------------
    normalized = (email.user_sdwt_prod or "").strip()
    if normalized in {"", UNASSIGNED_USER_SDWT_PROD, "rp-unclassified"}:
        return False

    # -----------------------------------------------------------------------------
    # 3) 최종 판단
    # -----------------------------------------------------------------------------
    return True


def claim_email_asset_ocr_tasks(
    *,
    limit: int,
    lease_seconds: int,
    max_attempts: int,
    worker_id: str | None = None,
) -> list[Dict[str, Any]]:
    """OCR 처리 대상 EmailAsset을 클레임하고 작업 정보를 반환합니다.

    입력:
        limit: 최대 클레임 개수.
        lease_seconds: 작업 잠금 유지 시간(초).
        max_attempts: 최대 시도 횟수.
        worker_id: 작업자 식별자(옵션).
    반환:
        OCR 작업 정보 리스트.
    부작용:
        EmailAsset의 OCR 상태/락 정보가 갱신됩니다.
    오류:
        DB 오류 발생 시 예외가 전파될 수 있습니다.
    """

    # -----------------------------------------------------------------------------
    # 1) 입력 정규화
    # -----------------------------------------------------------------------------
    if not isinstance(limit, int) or limit <= 0:
        return []
    if not isinstance(lease_seconds, int) or lease_seconds <= 0:
        return []
    if not isinstance(max_attempts, int) or max_attempts <= 0:
        return []

    normalized_worker = worker_id.strip() if isinstance(worker_id, str) and worker_id.strip() else None
    now = timezone.now()
    lease_expires_at = now + timedelta(seconds=lease_seconds)
    bucket = getattr(settings, "MINIO_BUCKET", "") or ""

    # -----------------------------------------------------------------------------
    # 2) 대상 자산 선별 및 락 부여
    # -----------------------------------------------------------------------------
    tasks: list[Dict[str, Any]] = []
    with transaction.atomic():
        assets = list_claimable_email_assets_for_update(
            now=now,
            max_attempts=max_attempts,
            limit=limit,
        )

        for asset in assets:
            lock_token = secrets.token_hex(16)
            asset.ocr_status = EmailAsset.OcrStatus.PROCESSING
            asset.ocr_lock_token = lock_token
            asset.ocr_lock_expires_at = lease_expires_at
            asset.ocr_worker_id = normalized_worker
            asset.ocr_attempt_count = (asset.ocr_attempt_count or 0) + 1
            asset.ocr_attempted_at = now
            asset.ocr_completed_at = None
            asset.ocr_text = ""
            asset.ocr_error_code = ""
            asset.ocr_error_message = ""
            asset.ocr_error = ""
            asset.ocr_model = None
            asset.ocr_duration_ms = None

            asset.save(
                update_fields=[
                    "ocr_status",
                    "ocr_lock_token",
                    "ocr_lock_expires_at",
                    "ocr_worker_id",
                    "ocr_attempt_count",
                    "ocr_attempted_at",
                    "ocr_completed_at",
                    "ocr_text",
                    "ocr_error_code",
                    "ocr_error_message",
                    "ocr_error",
                    "ocr_model",
                    "ocr_duration_ms",
                ]
            )

            tasks.append(
                {
                    "asset_id": asset.id,
                    "email_id": asset.email_id,
                    "sequence": asset.sequence,
                    "source_type": asset.source,
                    "object_key": asset.object_key,
                    "bucket": bucket,
                    "external_url": asset.original_url,
                    "content_type": asset.content_type,
                    "size_bytes": asset.byte_size,
                    "lock_token": lock_token,
                    "lock_expires_at": lease_expires_at.isoformat(),
                    "attempt_count": asset.ocr_attempt_count,
                }
            )

    # -----------------------------------------------------------------------------
    # 3) 결과 반환
    # -----------------------------------------------------------------------------
    return tasks


def update_email_asset_ocr_results(*, results: Sequence[Dict[str, Any]], max_attempts: int) -> Dict[str, int]:
    """OCR 결과를 EmailAsset에 반영하고 RAG 재인덱싱을 요청합니다.

    입력:
        results: OCR 결과 목록(asset_id/lock_token/status/text/error_code/error_message/ocr_model/ocr_duration_ms).
        max_attempts: 최대 시도 횟수.
    반환:
        {"updated": int, "rejected": int, "ragQueued": int, "ragFailed": int, "ragSkipped": int} 형태의 카운트
    부작용:
        - EmailAsset 업데이트
        - Email RAG Outbox 적재
    오류:
        DB 오류 발생 시 예외가 전파될 수 있습니다.
    """

    # -----------------------------------------------------------------------------
    # 1) 입력 검증
    # -----------------------------------------------------------------------------
    if not results:
        return {"updated": 0, "rejected": 0, "ragQueued": 0, "ragFailed": 0, "ragSkipped": 0}
    if not isinstance(max_attempts, int) or max_attempts <= 0:
        return {"updated": 0, "rejected": len(results), "ragQueued": 0, "ragFailed": 0, "ragSkipped": 0}

    updated = 0
    rejected = 0
    email_ids: set[int] = set()
    now = timezone.now()

    # -----------------------------------------------------------------------------
    # 2) OCR 결과 업데이트
    # -----------------------------------------------------------------------------
    with transaction.atomic():
        for item in results:
            asset_id = item.get("asset_id")
            lock_token = item.get("lock_token")
            status = item.get("status")

            if not isinstance(asset_id, int) or not isinstance(lock_token, str) or not lock_token.strip():
                rejected += 1
                continue
            if status not in {EmailAsset.OcrStatus.DONE, EmailAsset.OcrStatus.FAILED}:
                rejected += 1
                continue

            asset = get_email_asset_by_id(asset_id=asset_id)
            if asset is None:
                rejected += 1
                continue

            if asset.ocr_status != EmailAsset.OcrStatus.PROCESSING:
                rejected += 1
                continue
            if (asset.ocr_lock_token or "") != lock_token.strip():
                rejected += 1
                continue
            if asset.ocr_lock_expires_at and asset.ocr_lock_expires_at < now:
                rejected += 1
                continue

            resolved_status = status
            if asset.source == EmailAsset.Source.EXTERNAL_URL and status == EmailAsset.OcrStatus.FAILED:
                resolved_status = EmailAsset.OcrStatus.DONE

            processed_at = item.get("processed_at") if item.get("processed_at") else now
            text = item.get("text") or ""
            error_code = item.get("error_code") or ""
            error_message = item.get("error_message") or ""
            ocr_model = item.get("ocr_model") or ""
            duration_ms = item.get("ocr_duration_ms")

            update_fields: list[str] = [
                "ocr_status",
                "ocr_text",
                "ocr_error_code",
                "ocr_error_message",
                "ocr_error",
                "ocr_model",
                "ocr_completed_at",
                "ocr_lock_token",
                "ocr_lock_expires_at",
                "ocr_worker_id",
            ]

            asset.ocr_status = resolved_status
            asset.ocr_text = text
            asset.ocr_error_code = error_code
            asset.ocr_error_message = error_message
            asset.ocr_error = error_message
            asset.ocr_model = ocr_model
            asset.ocr_completed_at = processed_at
            asset.ocr_lock_token = None
            asset.ocr_lock_expires_at = None
            asset.ocr_worker_id = None

            if duration_ms is not None:
                asset.ocr_duration_ms = duration_ms
                update_fields.append("ocr_duration_ms")

            asset.save(update_fields=update_fields)
            updated += 1
            email_ids.add(asset.email_id)

    # -----------------------------------------------------------------------------
    # 3) RAG 재인덱싱 큐 적재
    # -----------------------------------------------------------------------------
    rag_queued = 0
    rag_failed = 0
    rag_skipped = 0
    for email_id in email_ids:
        if has_unprocessed_email_assets(email_id=email_id, max_attempts=max_attempts):
            continue
        email = get_email_by_id(email_id=email_id)
        if email is None:
            continue
        if not _should_enqueue_rag(email=email):
            rag_skipped += 1
            continue
        try:
            enqueue_rag_index(email=email)
            rag_queued += 1
        except Exception:
            logger.exception("Failed to enqueue OCR RAG update (email_id=%s)", email_id)
            rag_failed += 1

    return {
        "updated": updated,
        "rejected": rejected,
        "ragQueued": rag_queued,
        "ragFailed": rag_failed,
        "ragSkipped": rag_skipped,
    }


__all__ = ["claim_email_asset_ocr_tasks", "update_email_asset_ocr_results"]
