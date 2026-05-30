"""m_tkin_prevent 읽기 전용 selector입니다."""

from __future__ import annotations

from django.db.models import QuerySet

from api.data_movement.m_tkin_prevent.models import MTkinPreventLoadJob


def list_recent_load_jobs(*, limit: int = 20) -> QuerySet[MTkinPreventLoadJob]:
    """최근 적재 이력을 최신순으로 반환합니다."""

    return MTkinPreventLoadJob.objects.order_by("-created_at", "-id")[:limit]
