# =============================================================================
# 모듈 설명: AppStore 댓글 서비스 로직을 제공합니다.
# - 주요 함수: create_comment, update_comment, toggle_comment_like
# - 불변 조건: like_count는 원자적으로 갱신합니다.
# =============================================================================
from __future__ import annotations

from typing import Any, Tuple

from django.db import transaction
from django.db.models import F
from django.db.models.functions import Greatest

from ..selectors import get_comment_by_id, get_comment_like_count
from ..models import AppStoreApp, AppStoreComment, AppStoreCommentLike


def create_comment(
    *,
    app: AppStoreApp,
    user: Any,
    content: str,
    parent_comment: AppStoreComment | None = None,
) -> AppStoreComment:
    """앱에 댓글을 생성합니다.

    인자:
        app: 대상 앱 인스턴스.
        user: Django 사용자 인스턴스.
        content: 댓글 본문.
        parent_comment: 부모 댓글(대댓글) 인스턴스.

    반환:
        생성된 댓글 인스턴스(재조회 시도).

    부작용:
        AppStoreComment 레코드를 생성합니다.

    오류:
        부모 댓글이 다른 앱에 속하면 ValueError를 발생시킵니다.
    """

    # -----------------------------------------------------------------------------
    # 1) 부모 댓글 유효성 확인
    # -----------------------------------------------------------------------------
    if parent_comment and parent_comment.app_id != app.pk:
        raise ValueError("Parent comment must belong to the same app.")

    # -----------------------------------------------------------------------------
    # 2) 댓글 생성 및 재조회
    # -----------------------------------------------------------------------------
    comment = AppStoreComment.objects.create(app=app, user=user, content=content, parent=parent_comment)
    return get_comment_by_id(app_id=app.pk, comment_id=comment.pk) or comment


def update_comment(*, comment: AppStoreComment, content: str) -> AppStoreComment:
    """댓글 내용을 수정합니다.

    인자:
        comment: 대상 댓글 인스턴스.
        content: 새로운 댓글 본문.

    반환:
        업데이트된 댓글 인스턴스(재조회 시도).

    부작용:
        AppStoreComment.content를 갱신합니다.

    오류:
        ORM 저장 과정에서 예외가 발생할 수 있습니다.
    """

    comment.content = content
    comment.save(update_fields=["content", "updated_at"])
    return get_comment_by_id(app_id=comment.app_id, comment_id=comment.pk) or comment


def delete_comment(*, comment: AppStoreComment) -> None:
    """댓글을 삭제합니다.

    인자:
        comment: 대상 댓글 인스턴스.

    반환:
        없음.

    부작용:
        AppStoreComment 레코드를 삭제합니다.

    오류:
        ORM 삭제 과정에서 예외가 발생할 수 있습니다.
    """

    comment.delete()


@transaction.atomic
def toggle_comment_like(*, comment: AppStoreComment, user: Any) -> Tuple[bool, int]:
    """댓글 좋아요를 토글하고 like_count를 갱신합니다.

    인자:
        comment: 대상 댓글 인스턴스.
        user: 요청 사용자 인스턴스.

    반환:
        (liked, like_count) 튜플.

    부작용:
        AppStoreCommentLike 생성/삭제 및 like_count 갱신이 발생합니다.

    오류:
        ORM 저장 과정에서 예외가 발생할 수 있습니다.
    """

    # -----------------------------------------------------------------------------
    # 1) 좋아요 토글(행 잠금)
    # -----------------------------------------------------------------------------
    like, created = AppStoreCommentLike.objects.select_for_update().get_or_create(comment=comment, user=user)
    if created:
        AppStoreComment.objects.filter(pk=comment.pk).update(like_count=F("like_count") + 1)
        liked = True
    else:
        like.delete()
        AppStoreComment.objects.filter(pk=comment.pk).update(like_count=Greatest(F("like_count") - 1, 0))
        liked = False

    # -----------------------------------------------------------------------------
    # 2) 최신 like_count 재조회
    # -----------------------------------------------------------------------------
    like_count = get_comment_like_count(app_id=comment.app_id, comment_id=comment.pk)
    return liked, like_count
