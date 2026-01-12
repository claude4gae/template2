# =============================================================================
# 모듈 설명: AppStore 조회 셀렉터를 제공합니다.
# - 주요 함수: get_app_list, get_app_detail, get_comments_for_app
# - 불변 조건: 조회는 읽기 전용이며 최신순/오래된 순 정렬을 유지합니다.
# =============================================================================
from __future__ import annotations

from typing import Any

from django.db.models import Count, QuerySet

from .models import AppStoreApp, AppStoreComment, AppStoreCommentLike, AppStoreLike


def get_app_list() -> QuerySet[AppStoreApp]:
    """AppStore 앱 목록 조회용 QuerySet을 반환합니다.

    반환:
        최신순으로 정렬되고 comment_count가 포함된 QuerySet.

    부작용:
        없음. 읽기 전용 조회입니다.

    오류:
        없음.
    """

    return (
        AppStoreApp.objects.select_related("owner")
        .annotate(comment_count=Count("comments"))
        .order_by("-created_at", "-id")
    )


def get_app_by_id(*, app_id: int) -> AppStoreApp | None:
    """앱 단건(소유자/댓글수 포함)을 조회합니다.

    인자:
        app_id: 앱 PK.

    반환:
        AppStoreApp 인스턴스 또는 None.

    부작용:
        없음. 읽기 전용 조회입니다.

    오류:
        없음(미존재 시 None 반환).
    """

    # -----------------------------------------------------------------------------
    # 1) 앱 단건 조회(없으면 None 반환)
    # -----------------------------------------------------------------------------
    try:
        return (
            AppStoreApp.objects.select_related("owner")
            .annotate(comment_count=Count("comments"))
            .get(pk=app_id)
        )
    except AppStoreApp.DoesNotExist:
        return None


def get_app_detail(*, app_id: int) -> AppStoreApp | None:
    """상세 화면용으로 댓글까지 prefetch한 앱을 조회합니다.

    인자:
        app_id: 앱 PK.

    반환:
        AppStoreApp 인스턴스 또는 None.

    부작용:
        없음. 읽기 전용 조회입니다.

    오류:
        없음(미존재 시 None 반환).
    """

    # -----------------------------------------------------------------------------
    # 1) 댓글 prefetch 포함 단건 조회
    # -----------------------------------------------------------------------------
    try:
        return (
            AppStoreApp.objects.select_related("owner")
            .prefetch_related("comments__user")
            .annotate(comment_count=Count("comments"))
            .get(pk=app_id)
        )
    except AppStoreApp.DoesNotExist:
        return None


def get_app_like_count(*, app_id: int) -> int:
    """앱 좋아요 수를 조회합니다.

    인자:
        app_id: 앱 PK.

    반환:
        좋아요 수 정수 값.

    부작용:
        없음. 읽기 전용 조회입니다.

    오류:
        없음.
    """

    # -----------------------------------------------------------------------------
    # 1) 좋아요 수 조회
    # -----------------------------------------------------------------------------
    value = AppStoreApp.objects.filter(pk=app_id).values_list("like_count", flat=True).first()
    return int(value or 0)


def get_app_view_count(*, app_id: int) -> int:
    """앱 조회수를 조회합니다.

    인자:
        app_id: 앱 PK.

    반환:
        조회수 정수 값.

    부작용:
        없음. 읽기 전용 조회입니다.

    오류:
        없음.
    """

    # -----------------------------------------------------------------------------
    # 1) 조회수 조회
    # -----------------------------------------------------------------------------
    value = AppStoreApp.objects.filter(pk=app_id).values_list("view_count", flat=True).first()
    return int(value or 0)


def get_liked_app_ids_for_user(*, user: Any) -> list[int]:
    """사용자가 좋아요한 앱 id 목록을 반환합니다.

    인자:
        user: Django 사용자 객체.

    반환:
        좋아요한 앱 id 목록.

    부작용:
        없음. 읽기 전용 조회입니다.

    오류:
        없음.
    """

    return list(AppStoreLike.objects.filter(user=user).values_list("app_id", flat=True))


def get_liked_comment_ids_for_user(*, user: Any, app_id: int) -> list[int]:
    """사용자가 좋아요한 댓글 id 목록을 반환합니다.

    인자:
        user: Django 사용자 객체.
        app_id: 앱 PK.

    반환:
        해당 앱에서 사용자가 좋아요한 댓글 id 목록.

    부작용:
        없음. 읽기 전용 조회입니다.

    오류:
        없음.
    """

    return list(
        AppStoreCommentLike.objects.filter(user=user, comment__app_id=app_id).values_list("comment_id", flat=True)
    )


def get_comments_for_app(*, app_id: int) -> QuerySet[AppStoreComment]:
    """앱의 댓글 목록을 오래된 순으로 조회합니다.

    인자:
        app_id: 앱 PK.

    반환:
        댓글 QuerySet(오래된 순 정렬).

    부작용:
        없음. 읽기 전용 조회입니다.

    오류:
        없음.
    """

    return (
        AppStoreComment.objects.filter(app_id=app_id)
        .select_related("user")
        .order_by("created_at", "id")
    )


def get_comment_like_count(*, app_id: int, comment_id: int) -> int:
    """댓글 좋아요 수를 조회합니다.

    인자:
        app_id: 앱 PK.
        comment_id: 댓글 PK.

    반환:
        좋아요 수 정수 값.

    부작용:
        없음. 읽기 전용 조회입니다.

    오류:
        없음.
    """

    # -----------------------------------------------------------------------------
    # 1) 댓글 좋아요 수 조회
    # -----------------------------------------------------------------------------
    value = (
        AppStoreComment.objects.filter(pk=comment_id, app_id=app_id)
        .values_list("like_count", flat=True)
        .first()
    )
    return int(value or 0)


def get_comment_by_id(*, app_id: int, comment_id: int) -> AppStoreComment | None:
    """앱의 댓글 단건을 조회합니다.

    인자:
        app_id: 앱 PK.
        comment_id: 댓글 PK.

    반환:
        AppStoreComment 인스턴스 또는 None.

    부작용:
        없음. 읽기 전용 조회입니다.

    오류:
        없음(미존재 시 None 반환).
    """

    # -----------------------------------------------------------------------------
    # 1) 댓글 단건 조회(없으면 None 반환)
    # -----------------------------------------------------------------------------
    try:
        return AppStoreComment.objects.select_related("user", "app").get(pk=comment_id, app_id=app_id)
    except AppStoreComment.DoesNotExist:
        return None
