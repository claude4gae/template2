# =============================================================================
# 모듈 설명: voc 응답 직렬화 유틸을 제공합니다.
# - 주요 함수: serialize_user, serialize_reply, serialize_post
# - 불변 조건: 응답 키는 카멜 케이스 기준을 유지합니다.
# =============================================================================

from __future__ import annotations

from typing import Any, Iterable


def serialize_user(user: Any) -> dict[str, Any] | None:
    """작성자 정보를 API 응답 형태로 직렬화합니다.

    입력:
    - user: 사용자 객체 또는 None

    반환:
    - dict[str, Any] | None: 작성자 payload(없으면 None)

    부작용:
    - 없음

    오류:
    - 없음
    """

    # -----------------------------------------------------------------------------
    # 1) 사용자 유무 및 이름 구성
    # -----------------------------------------------------------------------------
    if not user:
        return None
    name = (user.get_full_name() or "").strip() or user.get_username() or user.email
    payload: dict[str, Any] = {"id": user.pk, "name": name or "사용자"}
    # -----------------------------------------------------------------------------
    # 2) 이메일 포함 여부 결정
    # -----------------------------------------------------------------------------
    if user.email:
        payload["email"] = user.email
    return payload


def serialize_reply(reply: Any) -> dict[str, Any]:
    """답변(VocReply)을 API 응답 형태로 직렬화합니다.

    입력:
    - reply: VocReply 객체

    반환:
    - dict[str, Any]: 답변 응답 payload

    부작용:
    - 없음

    오류:
    - 없음
    """

    return {
        "id": reply.pk,
        "postId": reply.post_id,
        "content": reply.content,
        "createdAt": reply.created_at.isoformat(),
        "author": serialize_user(getattr(reply, "author", None)),
    }


def _prefetched_replies(post: Any) -> Iterable[dict[str, Any]]:
    """prefetch_related 결과를 활용해 답변을 직렬화합니다.

    입력:
    - post: VocPost 객체(가능하면 replies가 prefetched된 상태)

    반환:
    - Iterable[dict[str, Any]]: 답변 payload 목록

    부작용:
    - 없음

    오류:
    - 없음
    """

    related = getattr(post, "replies", None)
    if related is None:
        return []
    return [serialize_reply(reply) for reply in related.all()]


def serialize_post(post: Any) -> dict[str, Any]:
    """게시글(VocPost)을 API 응답 형태로 직렬화합니다.

    입력:
    - post: VocPost 객체

    반환:
    - dict[str, Any]: 게시글 응답 payload

    부작용:
    - 없음

    오류:
    - 없음
    """

    return {
        "id": post.pk,
        "title": post.title,
        "content": post.content,
        "status": post.status,
        "app": post.app,
        "createdAt": post.created_at.isoformat(),
        "updatedAt": post.updated_at.isoformat(),
        "author": serialize_user(getattr(post, "author", None)),
        "replies": list(_prefetched_replies(post)),
    }


__all__ = ["serialize_post", "serialize_reply", "serialize_user"]
