# =============================================================================
# 모듈: Drone SOP Jira 상태 반영
# 주요 기능: Jira 성공 delivery metadata와 legacy status update 호환 처리
# 주요 가정: Jira API 호출 결과는 delivery id/key 매핑으로 전달됩니다.
# =============================================================================
"""Drone SOP Jira 상태 반영 헬퍼 모듈입니다."""

from __future__ import annotations

from typing import Any, Sequence

from django.db import transaction
from django.utils import timezone

from ...models import DroneSOP, DroneSopDelivery
from ..shared.delivery_snapshot import is_sop_delivery_eligible
from ..shared.delivery_state import (
    ensure_channel_delivery_snapshots_for_rows,
    mark_channel_delivery_status,
    normalize_positive_ids,
    prepare_channel_delivery_for_row,
)


def _normalize_string_value(value: Any) -> str | None:
    """문자열 값을 공백 제거 기준으로 정규화합니다."""

    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned if cleaned else None


def update_drone_sop_jira_summary(
    *,
    delivery_ids: Sequence[int],
    key_by_delivery_id: dict[int, str] | None = None,
    step_by_delivery_id: dict[int, str] | None = None,
) -> int:
    """Jira delivery 성공 메타데이터를 delivery row에 반영합니다."""

    # -------------------------------------------------------------------------
    # 1) delivery → SOP 매핑 확인
    # -------------------------------------------------------------------------
    normalized_delivery_ids = normalize_positive_ids(delivery_ids)
    if not normalized_delivery_ids:
        return 0

    delivery_rows = list(
        DroneSopDelivery.objects.filter(id__in=normalized_delivery_ids).values("id", "sop_id")
    )
    if not delivery_rows:
        return 0

    # -------------------------------------------------------------------------
    # 2) 단계/키 매핑 구성
    # -------------------------------------------------------------------------
    step_source = step_by_delivery_id or {}
    sop_ids: list[int] = []
    step_by_id: dict[int, str] = {}
    for row in delivery_rows:
        delivery_id = row.get("id")
        sop_id = row.get("sop_id")
        if not isinstance(delivery_id, int) or not isinstance(sop_id, int):
            continue
        if sop_id not in sop_ids:
            sop_ids.append(sop_id)
        step = step_source.get(delivery_id)
        if isinstance(step, str) and step.strip():
            step_by_id[delivery_id] = step.strip()
    if not sop_ids:
        return 0

    # -------------------------------------------------------------------------
    # 3) delivery별 step snapshot 보정
    # -------------------------------------------------------------------------
    with transaction.atomic():
        for delivery_id, sent_step in step_by_id.items():
            DroneSopDelivery.objects.filter(id=delivery_id).update(
                sent_step=sent_step,
                updated_at=timezone.now(),
            )
    return len(sop_ids)


def update_drone_sop_jira_status(
    *,
    done_ids: Sequence[int],
    rows: Sequence[dict[str, Any]],
    key_by_id: dict[int, str],
) -> int:
    """Jira 생성 완료된 SOP의 Jira delivery를 성공으로 표시합니다."""

    normalized_done_ids = normalize_positive_ids(list(done_ids))
    if not normalized_done_ids:
        return 0

    candidate_rows = [row for row in rows if isinstance(row.get("id"), int) and int(row["id"]) in normalized_done_ids]
    if not candidate_rows:
        return 0

    current_state_by_id = {
        int(row["id"]): row
        for row in DroneSOP.objects.filter(id__in=[int(row["id"]) for row in candidate_rows]).values(
            "id",
            "sdwt_prod",
            "user_sdwt_prod",
            "target_user_sdwt_prod",
            "status",
            "needtosend",
            "instant_inform",
        )
    }
    candidate_rows = [
        {**row, **current_state}
        for row in candidate_rows
        if (current_state := current_state_by_id.get(int(row["id"]))) is not None
    ]
    if not candidate_rows:
        return 0

    existing_delivery_sop_ids = set(
        DroneSopDelivery.objects.filter(
            sop_id__in=[int(row["id"]) for row in candidate_rows],
            channel=DroneSopDelivery.Channels.JIRA,
        ).values_list("sop_id", flat=True)
    )

    eligible_rows = [row for row in candidate_rows if is_sop_delivery_eligible(row)]
    status_rows = [
        row
        for row in candidate_rows
        if is_sop_delivery_eligible(row) or int(row["id"]) in existing_delivery_sop_ids
    ]
    if not status_rows:
        return 0
    status_sop_ids = [int(row["id"]) for row in status_rows]

    if eligible_rows:
        ensure_channel_delivery_snapshots_for_rows(
            rows=list(eligible_rows),
            channels=[DroneSopDelivery.Channels.JIRA],
        )
    for row in eligible_rows:
        sop_id = row.get("id")
        target = _normalize_string_value(row.get("target_user_sdwt_prod")) or "__TARGET_MISSING__"
        if isinstance(sop_id, int):
            prepare_channel_delivery_for_row(
                row=row,
                target_user_sdwt_prod=target,
                channel=DroneSopDelivery.Channels.JIRA,
            )
    pending_delivery_rows = list(
        DroneSopDelivery.objects.filter(
            sop_id__in=status_sop_ids,
            channel=DroneSopDelivery.Channels.JIRA,
        )
        .exclude(status=DroneSopDelivery.Statuses.SUCCESS)
        .order_by("sop_id", "id")
        .values("id", "sop_id")
    )
    if not pending_delivery_rows:
        return 0

    delivery_ids = [int(row["id"]) for row in pending_delivery_rows if isinstance(row.get("id"), int)]
    key_by_delivery_id = {
        int(row["id"]): key_by_id[int(row["sop_id"])]
        for row in pending_delivery_rows
        if isinstance(row.get("id"), int)
        and isinstance(row.get("sop_id"), int)
        and isinstance(key_by_id.get(int(row["sop_id"])), str)
    }
    step_by_sop_id: dict[int, str] = {}
    sent_comment_by_sop_id: dict[int, Any] = {}
    for row in status_rows:
        sop_id = int(row["id"])
        step = _normalize_string_value(row.get("metro_current_step"))
        if step:
            step_by_sop_id[sop_id] = step
        sent_comment_by_sop_id[sop_id] = row.get("comment")
    step_by_delivery_id = {
        int(row["id"]): step_by_sop_id[int(row["sop_id"])]
        for row in pending_delivery_rows
        if isinstance(row.get("id"), int)
        and isinstance(row.get("sop_id"), int)
        and int(row["sop_id"]) in step_by_sop_id
    }
    sent_comment_by_delivery_id = {
        int(row["id"]): sent_comment_by_sop_id[int(row["sop_id"])]
        for row in pending_delivery_rows
        if isinstance(row.get("id"), int)
        and isinstance(row.get("sop_id"), int)
        and int(row["sop_id"]) in sent_comment_by_sop_id
    }

    mark_channel_delivery_status(
        delivery_ids=delivery_ids,
        status=DroneSopDelivery.Statuses.SUCCESS,
        external_key_by_id=key_by_delivery_id,
        sent_comment_by_id=sent_comment_by_delivery_id,
    )
    return update_drone_sop_jira_summary(
        delivery_ids=delivery_ids,
        key_by_delivery_id=key_by_delivery_id,
        step_by_delivery_id=step_by_delivery_id,
    )


__all__ = ["update_drone_sop_jira_status", "update_drone_sop_jira_summary"]
