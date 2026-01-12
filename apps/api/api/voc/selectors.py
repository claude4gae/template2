# =============================================================================
# 모듈 설명: voc 읽기 전용 셀렉터를 제공합니다.
# - 주요 함수: get_post_list, get_post_detail, get_status_counts 등
# - 불변 조건: 모든 쿼리는 읽기 전용입니다.
# =============================================================================

from __future__ import annotations

from typing import Any

from django.db.models import Count, QuerySet

from .models import VocPost, VocReply


def get_valid_post_statuses() -> set[str]:
    """VocPost.status로 사용할 수 있는 값 집합을 반환합니다.

    입력:
    - 없음

    반환:
    - set[str]: VocPost.status 허용 값 집합

    부작용:
    - 없음(읽기 전용)

    오류:
    - 없음
    """

    return {choice[0] for choice in VocPost.Status.choices}


def get_default_post_status() -> str:
    """신규 VOC 게시글의 기본 상태 값을 반환합니다.

    입력:
    - 없음

    반환:
    - str: 기본 상태 값

    부작용:
    - 없음

    오류:
    - 없음
    """

    return VocPost.Status.RECEIVED


def get_post_list(*, status: str | None = None) -> QuerySet[VocPost]:
    """VOC 게시글 목록을 조회합니다(선택적으로 status 필터 적용).

    입력:
    - status: 상태 필터(선택)

    반환:
    - QuerySet[VocPost]: author/replies를 prefetch한 게시글 목록

    부작용:
    - 없음(읽기 전용 쿼리)

    오류:
    - 없음
    """

    queryset = (
        VocPost.objects.select_related("author")
        .prefetch_related("replies__author")
        .order_by("-created_at", "-id")
    )
    if status:
        queryset = queryset.filter(status=status)
    return queryset


def get_post_detail(*, post_id: int) -> VocPost | None:
    """답변까지 prefetch한 VOC 게시글 단건을 조회합니다.

    입력:
    - post_id: VocPost 기본 키

    반환:
    - VocPost | None: 게시글(없으면 None)

    부작용:
    - 없음(읽기 전용 쿼리)

    오류:
    - 없음
    """

    try:
        return (
            VocPost.objects.select_related("author")
            .prefetch_related("replies__author")
            .get(pk=post_id)
        )
    except VocPost.DoesNotExist:
        return None


def get_reply_by_id(*, reply_id: int) -> VocReply | None:
    """author/post를 select_related한 답변 단건을 조회합니다.

    입력:
    - reply_id: VocReply 기본 키

    반환:
    - VocReply | None: 답변(없으면 None)

    부작용:
    - 없음(읽기 전용 쿼리)

    오류:
    - 없음
    """

    try:
        return VocReply.objects.select_related("author", "post").get(pk=reply_id)
    except VocReply.DoesNotExist:
        return None


def get_status_counts() -> dict[str, int]:
    """VOC 게시글 상태(status)별 개수를 반환합니다.

    입력:
    - 없음

    반환:
    - dict[str, int]: 상태별 개수

    부작용:
    - 없음(읽기 전용 쿼리)

    오류:
    - 없음
    """

    valid_statuses = get_valid_post_statuses()
    base = {status: 0 for status in valid_statuses}

    # -----------------------------------------------------------------------------
    # 1) status 기준으로 정렬된 결과를 반영
    # -----------------------------------------------------------------------------
    for row in VocPost.objects.values("status").annotate(total=Count("id")).order_by("status"):
        status = row.get("status")
        if status in base:
            base[status] = int(row.get("total") or 0)

    # -----------------------------------------------------------------------------
    # 2) 응답 순서를 VocPost.Status.choices 기준으로 정렬
    # -----------------------------------------------------------------------------
    ordered: dict[str, int] = {}
    for status, _label in VocPost.Status.choices:
        if status in base:
            ordered[status] = base[status]
    return ordered


def is_admin_user(*, user: Any) -> bool:
    """사용자가 VOC 게시글을 관리할 권한이 있는지 반환합니다.

    입력:
    - user: 사용자 객체

    반환:
    - bool: 관리자 권한 여부

    부작용:
    - user.profile 조회(읽기 전용)

    오류:
    - 없음
    """

    # -----------------------------------------------------------------------------
    # 1) 기본 인증/관리자 플래그 확인
    # -----------------------------------------------------------------------------
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
        return True
    # -----------------------------------------------------------------------------
    # 2) 프로필 역할 확인
    # -----------------------------------------------------------------------------
    profile = getattr(user, "profile", None)
    role = getattr(profile, "role", None) if profile else None
    return role == "admin"
