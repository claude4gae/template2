# =============================================================================
# 모듈 설명: emails 서비스 상수를 제공합니다.
# - 주요 대상: SENT_MAILBOX_ID, EMAIL_CLASSIFICATION_*, EMAIL_RAG_INDEX_STATUS_*
# - 불변 조건: Email 모델 Enum 값과 동일해야 합니다.
# =============================================================================

"""emails 서비스 상수 모음.

- 주요 대상: SENT_MAILBOX_ID, EMAIL_CLASSIFICATION_*, EMAIL_RAG_INDEX_STATUS_*
- 주요 엔드포인트/클래스: 없음(상수 정의만 제공)
- 가정/불변 조건: Email 모델 Enum 값과 일치해야 함
"""

from __future__ import annotations

from ..models import Email

SENT_MAILBOX_ID = "__sent__"
EMAIL_CLASSIFICATION_CONFIRMED_USER = Email.ClassificationSource.CONFIRMED_USER
EMAIL_CLASSIFICATION_UNASSIGNED = Email.ClassificationSource.UNASSIGNED
EMAIL_RAG_INDEX_STATUS_INDEXED = Email.RagIndexStatus.INDEXED
EMAIL_RAG_INDEX_STATUS_PENDING = Email.RagIndexStatus.PENDING
EMAIL_RAG_INDEX_STATUS_SKIPPED = Email.RagIndexStatus.SKIPPED

__all__ = [
    "SENT_MAILBOX_ID",
    "EMAIL_CLASSIFICATION_CONFIRMED_USER",
    "EMAIL_CLASSIFICATION_UNASSIGNED",
    "EMAIL_RAG_INDEX_STATUS_INDEXED",
    "EMAIL_RAG_INDEX_STATUS_PENDING",
    "EMAIL_RAG_INDEX_STATUS_SKIPPED",
]
