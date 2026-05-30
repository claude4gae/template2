"""ctttm_workorder_list 읽기 전용 selector입니다."""

from __future__ import annotations

from django.db.models import QuerySet

from api.data_movement.ctttm_workorder_list.models import CtttmWorkorderListLoadJob


def list_recent_load_jobs(*, limit: int = 20) -> QuerySet[CtttmWorkorderListLoadJob]:
    """최근 적재 이력을 최신순으로 반환합니다."""

    return CtttmWorkorderListLoadJob.objects.order_by("-created_at", "-id")[:limit]
