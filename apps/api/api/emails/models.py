# =============================================================================
# 모듈 설명: 이메일 도메인 모델을 정의합니다.
# - 주요 클래스: Email, EmailOutbox
# - 불변 조건: db_table은 emails_* 접두어를 사용하며, 시간은 타임존 인지(timezone-aware)입니다.
# =============================================================================

from __future__ import annotations

from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils import timezone


class Email(models.Model):
    """수신 메일 저장 모델 (RAG doc 연동)."""

    class ClassificationSource(models.TextChoices):
        CONFIRMED_USER = "CONFIRMED_USER", "Confirmed User"
        PREDICTED_EXTERNAL = "PREDICTED_EXTERNAL", "Predicted External"
        UNASSIGNED = "UNASSIGNED", "Unassigned"

    class RagIndexStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        INDEXED = "INDEXED", "Indexed"
        SKIPPED = "SKIPPED", "Skipped"

    message_id = models.CharField(max_length=255, unique=True)
    received_at = models.DateTimeField()
    subject = models.TextField()
    sender = models.TextField()
    sender_id = models.CharField(max_length=50, db_index=True)  # KNOX ID(loginid) 등 발신자 식별자
    recipient = ArrayField(models.TextField(), null=True, blank=True)
    cc = ArrayField(models.TextField(), null=True, blank=True)
    participants_search = models.TextField(null=True, blank=True)

    user_sdwt_prod = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    classification_source = models.CharField(
        max_length=24,
        choices=ClassificationSource.choices,
        default=ClassificationSource.UNASSIGNED,
    )
    rag_index_status = models.CharField(
        max_length=16,
        choices=RagIndexStatus.choices,
        default=RagIndexStatus.SKIPPED,
    )

    body_text = models.TextField(blank=True)  # RAG 검색/스니펫용 텍스트
    body_html_object_key = models.CharField(max_length=512, null=True, blank=True)  # MinIO HTML 오브젝트 키

    rag_doc_id = models.CharField(max_length=255, null=True, blank=True, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "emails_inbox"
        indexes = [
            GinIndex(fields=["recipient"], name="idx_eml_inb_rcp_gin"),
            GinIndex(fields=["cc"], name="idx_eml_inb_cc_gin"),
            GinIndex(
                fields=["participants_search"],
                name="idx_eml_inb_par_trg",
                opclasses=["gin_trgm_ops"],
            ),
        ]

    # 사람이 읽기 위한 표현이므로 커버리지 제외
    def __str__(self) -> str:  # 테스트 제외(커버리지 제외): pragma: no cover
        """메일의 주요 필드를 간단한 문자열로 반환합니다.

        입력:
            없음(self만 사용).
        반환:
            제목/발신자/수신자/메일함 요약 문자열.
        부작용:
            없음.
        오류:
            없음.
        """

        recipient_text = ", ".join(self.recipient or [])
        return f"{self.subject[:40]} ({self.sender} -> {recipient_text}) [{self.user_sdwt_prod or ''}]"


class EmailOutbox(models.Model):
    """RAG 인덱싱/삭제 요청을 비동기 처리하기 위한 Outbox 모델."""

    class Action(models.TextChoices):
        INDEX = "INDEX", "Index"
        DELETE = "DELETE", "Delete"
        RECLASSIFY = "RECLASSIFY", "Reclassify"
        RECLASSIFY_ALL = "RECLASSIFY_ALL", "Reclassify All"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        DONE = "DONE", "Done"
        FAILED = "FAILED", "Failed"

    email = models.ForeignKey(Email, null=True, blank=True, on_delete=models.SET_NULL, related_name="outbox_items")
    action = models.CharField(max_length=16, choices=Action.choices)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    retry_count = models.PositiveIntegerField(default=0)
    available_at = models.DateTimeField(default=timezone.now)
    last_error = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "emails_outbox"
        indexes = [
            models.Index(fields=["status", "available_at"], name="idx_eml_out_sts_tm"),
        ]


class EmailAsset(models.Model):
    """이메일 HTML 내 이미지 자산 정보를 저장합니다."""

    class Source(models.TextChoices):
        CID = "CID", "CID"
        DATA_URL = "DATA_URL", "Data URL"
        EXTERNAL_URL = "EXTERNAL_URL", "External URL"

    class OcrStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        DONE = "DONE", "Done"
        FAILED = "FAILED", "Failed"

    email = models.ForeignKey(Email, on_delete=models.CASCADE, related_name="assets")
    sequence = models.PositiveIntegerField()
    object_key = models.CharField(max_length=512, null=True, blank=True)
    content_type = models.CharField(max_length=128, null=True, blank=True)
    byte_size = models.PositiveIntegerField(null=True, blank=True)
    source = models.CharField(max_length=16, choices=Source.choices)
    original_url = models.TextField(null=True, blank=True)
    ocr_status = models.CharField(max_length=16, choices=OcrStatus.choices, default=OcrStatus.PENDING)
    ocr_lock_token = models.CharField(max_length=64, null=True, blank=True)
    ocr_lock_expires_at = models.DateTimeField(null=True, blank=True)
    ocr_worker_id = models.CharField(max_length=64, null=True, blank=True)
    ocr_attempt_count = models.PositiveIntegerField(default=0)
    ocr_attempted_at = models.DateTimeField(null=True, blank=True)
    ocr_completed_at = models.DateTimeField(null=True, blank=True)
    ocr_text = models.TextField(blank=True)
    ocr_error_code = models.CharField(max_length=64, null=True, blank=True)
    ocr_error_message = models.TextField(blank=True, default="")
    ocr_error = models.TextField(blank=True)  # 레거시 호환용
    ocr_model = models.CharField(max_length=64, null=True, blank=True)
    ocr_duration_ms = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "emails_email_asset"
        constraints = [
            models.UniqueConstraint(
                fields=["email", "sequence"],
                name="uniq_eml_eml_ast_eml_seq",
            )
        ]
        indexes = [
            models.Index(fields=["email"], name="idx_eml_eml_ast_eml"),
            models.Index(fields=["ocr_status"], name="idx_eml_eml_ast_ocr_sts"),
            models.Index(
                fields=["ocr_lock_expires_at"],
                name="idx_eml_eml_ast_ocr_lk_exp_at",
            ),
        ]


__all__ = ["Email", "EmailAsset", "EmailOutbox"]
