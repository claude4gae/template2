# =============================================================================
# 모듈 설명: voc 게시글/답변 생성 및 수정 서비스를 제공합니다.
# - 주요 함수: create_post, update_post, delete_post, add_reply, can_manage_post
# - 불변 조건: 읽기 쿼리는 selectors를 통해 조회합니다.
# =============================================================================

from __future__ import annotations

from typing import Any, Dict, Tuple

from ..selectors import get_post_detail, get_reply_by_id, is_admin_user
from ..models import VocPost, VocReply


def create_post(*, author: Any, title: str, content: str, status: str, app: str) -> VocPost:
    """VOC 게시글을 생성하고 관계(prefetch)까지 포함해 반환합니다.

    입력:
    - author: 작성자 사용자 객체
    - title: 게시글 제목
    - content: 게시글 내용
    - status: 게시글 상태
    - app: 앱 카테고리

    반환:
    - VocPost: 관계가 로딩된 게시글

    부작용:
    - VocPost 레코드 생성

    오류:
    - 없음
    """

    post = VocPost.objects.create(
        title=title,
        content=content,
        status=status,
        app=app,
        author=author,
    )
    return get_post_detail(post_id=post.pk) or post


def update_post(*, post: VocPost, updates: Dict[str, Any]) -> VocPost:
    """VOC 게시글을 수정하고 관계(prefetch)까지 포함해 반환합니다.

    입력:
    - post: 대상 VocPost
    - updates: 업데이트 필드/값 맵(title/content/status/app)

    반환:
    - VocPost: 관계가 로딩된 게시글

    부작용:
    - VocPost 레코드 갱신

    오류:
    - 없음
    """

    for field, value in updates.items():
        setattr(post, field, value)
    post.save(update_fields=list(updates.keys()) + ["updated_at"])
    return get_post_detail(post_id=post.pk) or post


def delete_post(*, post: VocPost) -> None:
    """VOC 게시글을 삭제합니다.

    입력:
    - post: 대상 VocPost

    반환:
    - 없음

    부작용:
    - VocPost 레코드 삭제

    오류:
    - 없음
    """

    post.delete()


def add_reply(*, post: VocPost, author: Any, content: str) -> Tuple[VocReply, VocPost]:
    """게시글에 답변을 추가하고 (reply, refreshed_post)를 반환합니다.

    입력:
    - post: 대상 VocPost
    - author: 작성자 사용자 객체
    - content: 답변 내용

    반환:
    - Tuple[VocReply, VocPost]: (답변, 갱신된 게시글)

    부작용:
    - VocReply 레코드 생성

    오류:
    - 없음
    """

    reply = VocReply.objects.create(post=post, author=author, content=content)
    loaded_reply = get_reply_by_id(reply_id=reply.pk) or reply
    refreshed_post = get_post_detail(post_id=post.pk) or post
    return loaded_reply, refreshed_post


def can_manage_post(*, user: Any, post: VocPost) -> bool:
    """게시글 수정/삭제 가능 여부(관리자 또는 작성자)를 판별합니다.

    입력:
    - user: 사용자 객체
    - post: 대상 VocPost

    반환:
    - bool: 수정/삭제 가능 여부

    부작용:
    - 없음

    오류:
    - 없음
    """

    return is_admin_user(user=user) or (user and getattr(user, "pk", None) == post.author_id)
