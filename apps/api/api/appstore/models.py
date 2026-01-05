# =============================================================================
# 모듈 설명: AppStore 도메인 모델을 정의합니다.
# - 주요 클래스: AppStoreApp, AppStoreLike, AppStoreComment, AppStoreCommentLike
# - 불변 조건: 스크린샷은 외부 URL 또는 base64 data URL 형식을 사용합니다.
# =============================================================================
from __future__ import annotations

from django.conf import settings
from django.db import models


class AppStoreApp(models.Model):
    """내부 Appstore 앱 메타데이터."""

    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    url = models.TextField()
    screenshot_url = models.TextField(blank=True, default="")
    screenshot_base64 = models.TextField(blank=True, default="")
    screenshot_mime_type = models.CharField(max_length=100, blank=True, default="")
    screenshot_gallery = models.JSONField(default=list, blank=True)
    contact_name = models.CharField(max_length=255, blank=True, default="")
    contact_knoxid = models.CharField(max_length=255, blank=True, default="")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appstore_apps",
    )
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "appstore_app"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["category"], name="idx_aps_app_cat"),
            models.Index(fields=["name"], name="idx_aps_app_nam"),
        ]

    def __str__(self) -> str:  # 사람이 읽기 쉬운 표현(커버리지 제외): pragma: no cover
        """앱 표시용 문자열을 반환합니다."""
        return self.name

    @property
    def screenshot_src(self) -> str:
        """스크린샷 표시용 src(data URL 또는 외부 URL)를 반환합니다.

        입력:
            없음(self 사용).

        반환:
            화면 표시용 스크린샷 src 문자열.

        부작용:
            없음. 읽기 전용 계산입니다.

        오류:
            없음.
        """

        # -----------------------------------------------------------------------------
        # 1) 외부 URL 우선 사용
        # -----------------------------------------------------------------------------
        if self.screenshot_url:
            return self.screenshot_url

        # -----------------------------------------------------------------------------
        # 2) base64 데이터 URL 처리
        # -----------------------------------------------------------------------------
        if self.screenshot_base64:
            mime_type = self.screenshot_mime_type or "image/png"
            return f"data:{mime_type};base64,{self.screenshot_base64}"

        # -----------------------------------------------------------------------------
        # 3) 기본값
        # -----------------------------------------------------------------------------
        return ""

    def screenshot_gallery_srcs(self) -> list[str]:
        """갤러리(추가 스크린샷) 표시용 src 목록을 반환합니다.

        입력:
            없음(self 사용).

        반환:
            갤러리 스크린샷 src 목록.

        부작용:
            없음. 읽기 전용 계산입니다.

        오류:
            없음.
        """

        # -----------------------------------------------------------------------------
        # 1) 저장된 갤러리 데이터 확인
        # -----------------------------------------------------------------------------
        raw = self.screenshot_gallery
        if not isinstance(raw, list):
            return []

        # -----------------------------------------------------------------------------
        # 2) 항목별 URL/base64 정규화
        # -----------------------------------------------------------------------------
        srcs: list[str] = []
        for item in raw:
            if not isinstance(item, dict):
                continue

            url = item.get("url")
            if isinstance(url, str) and url.strip():
                srcs.append(url.strip())
                continue

            base64_value = item.get("base64")
            if isinstance(base64_value, str) and base64_value.strip():
                mime_type = item.get("mime_type")
                if not isinstance(mime_type, str) or not mime_type.strip():
                    mime_type = "image/png"
                srcs.append(f"data:{mime_type};base64,{base64_value.strip()}")

        # -----------------------------------------------------------------------------
        # 3) 결과 반환
        # -----------------------------------------------------------------------------
        return srcs

    def screenshot_srcs(self) -> list[str]:
        """대표 스크린샷 + 갤러리 스크린샷 src 목록을 반환합니다.

        입력:
            없음(self 사용).

        반환:
            대표 이미지 포함 스크린샷 src 목록.

        부작용:
            없음. 읽기 전용 계산입니다.

        오류:
            없음.
        """

        # -----------------------------------------------------------------------------
        # 1) 대표/갤러리 결합
        # -----------------------------------------------------------------------------
        cover = self.screenshot_src
        gallery = self.screenshot_gallery_srcs()
        if cover:
            return [cover, *gallery]
        return gallery


class AppStoreLike(models.Model):
    """앱 좋아요(토글) 기록."""

    app = models.ForeignKey(
        AppStoreApp,
        on_delete=models.CASCADE,
        related_name="likes",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="appstore_likes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "appstore_like"
        constraints = [
            models.UniqueConstraint(
                fields=["app", "user"],
                name="uniq_aps_lik_app_usr",
            ),
        ]
        indexes = [
            models.Index(fields=["user"], name="idx_aps_lik_usr"),
            models.Index(fields=["app"], name="idx_aps_lik_app"),
        ]

    def __str__(self) -> str:  # 사람이 읽기 쉬운 표현(커버리지 제외): pragma: no cover
        """좋아요 표시용 문자열을 반환합니다."""
        return f"{self.user_id} -> {self.app_id}"


class AppStoreComment(models.Model):
    """앱 댓글."""

    app = models.ForeignKey(
        AppStoreApp,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appstore_comments",
    )
    content = models.TextField()
    like_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "appstore_comment"
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(fields=["app"], name="idx_aps_cmt_app"),
            models.Index(fields=["app", "created_at"], name="idx_aps_cmt_app_crt_at"),
            models.Index(fields=["parent"], name="idx_aps_cmt_par"),
        ]

    def __str__(self) -> str:  # 사람이 읽기 쉬운 표현(커버리지 제외): pragma: no cover
        """댓글 표시용 문자열을 반환합니다."""
        return f"Comment {self.pk} on app {self.app_id}"


class AppStoreCommentLike(models.Model):
    """댓글 좋아요(토글) 기록."""

    comment = models.ForeignKey(
        AppStoreComment,
        on_delete=models.CASCADE,
        related_name="likes",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="appstore_comment_likes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "appstore_comment_like"
        constraints = [
            models.UniqueConstraint(
                fields=["comment", "user"],
                name="uniq_aps_cmt_lik_cmt_usr",
            ),
        ]
        indexes = [
            models.Index(fields=["user"], name="idx_aps_cmt_lik_usr"),
            models.Index(fields=["comment"], name="idx_aps_cmt_lik_cmt"),
        ]

    def __str__(self) -> str:  # 사람이 읽기 쉬운 표현(커버리지 제외): pragma: no cover
        """댓글 좋아요 표시용 문자열을 반환합니다."""
        return f"{self.user_id} -> {self.comment_id}"


__all__ = [
    "AppStoreApp",
    "AppStoreComment",
    "AppStoreCommentLike",
    "AppStoreLike",
]
