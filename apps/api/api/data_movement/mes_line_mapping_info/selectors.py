"""mes_line_mapping_info 읽기 전용 selector입니다."""

from __future__ import annotations

from django.db.models import QuerySet

from api.data_movement.mes_line_mapping_info.models import MesLineMappingInfoLoadJob


def list_recent_load_jobs(*, limit: int = 20) -> QuerySet[MesLineMappingInfoLoadJob]:
    """최근 적재 이력을 최신순으로 반환합니다."""

    return MesLineMappingInfoLoadJob.objects.order_by("-created_at", "-id")[:limit]
