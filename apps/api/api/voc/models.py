# =============================================================================
# 모듈 설명: voc 게시글/답변 모델을 정의합니다.
# - 주요 클래스: VocPost, VocReply
# - 불변 조건: db_table 접두사 규칙(voc_*)을 유지합니다.
# =============================================================================

from __future__ import annotations

from django.conf import settings
from django.db import models


class VocPost(models.Model):
    """VOC 게시글(제목/내용/상태/앱/작성자)을 저장하는 모델입니다."""

    class Status(models.TextChoices):
        RECEIVED = "접수", "접수"
        IN_PROGRESS = "진행중", "진행중"
        DONE = "완료", "완료"
        REJECTED = "반려", "반려"

    class AppCategory(models.TextChoices):
        OTHER = "기타", "기타"

    title = models.CharField(max_length=255)
    content = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.RECEIVED)
    app = models.CharField(
        max_length=80,
        choices=AppCategory.choices,
        default=AppCategory.OTHER,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="voc_posts",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "voc_post"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # 사람이 읽는 표현: pragma: no cover
        """사람이 읽기 쉬운 게시글 문자열 표현을 반환합니다."""
        return f"[{self.status}] {self.title}"


class VocReply(models.Model):
    """VOC 게시글에 대한 답변(댓글) 모델입니다."""

    post = models.ForeignKey(VocPost, on_delete=models.CASCADE, related_name="replies")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="voc_replies",
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "voc_reply"
        ordering = ["created_at"]

    def __str__(self) -> str:  # 사람이 읽는 표현: pragma: no cover
        """사람이 읽기 쉬운 답변 문자열 표현을 반환합니다."""
        return f"Reply to {self.post_id}"


__all__ = ["VocPost", "VocReply"]
