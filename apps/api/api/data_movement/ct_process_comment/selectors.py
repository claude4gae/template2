"""ct_process_comment 읽기 전용 selector입니다."""

from __future__ import annotations

from django.db.models import QuerySet

from api.data_movement.ct_process_comment.models import CtProcessCommentLoadJob


def list_recent_load_jobs(*, limit: int = 20) -> QuerySet[CtProcessCommentLoadJob]:
    """최근 적재 이력을 최신순으로 반환합니다."""

    return CtProcessCommentLoadJob.objects.order_by("-created_at", "-id")[:limit]
