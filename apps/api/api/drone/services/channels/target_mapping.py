"""Drone SOP 알림 target mapping 생성 서비스."""

from __future__ import annotations

from typing import Any

from django.db import IntegrityError, transaction

from ... import selectors
from ...models import DroneSopUserSdwtChannel, DroneSopUserSdwtProdMap
from .normalization import normalize_required_mapping_value as _normalize_required_mapping_value
from .user_sdwt_channel import ensure_drone_sop_notification_target


class DroneSopTargetMappingDuplicateError(ValueError):
    """이미 활성화된 target mapping이 있을 때 발생하는 오류입니다."""


def create_drone_sop_target_mapping(
    *,
    line_id: str,
    target_user_sdwt_prod: str,
    sdwt_prod: str,
    user_sdwt_prod: str,
    actor: Any | None = None,
) -> DroneSopUserSdwtProdMap:
    """sdwt_prod/user_sdwt_prod 조합을 target_user_sdwt_prod에 연결합니다.

    입력:
    - line_id: target 소유 라인
    - target_user_sdwt_prod: 알림 target 식별자
    - sdwt_prod: 설비 분임조 값
    - user_sdwt_prod: 사용자 분임조 값
    - actor: 생성 요청 사용자

    반환:
    - 생성 또는 재활성화된 DroneSopUserSdwtProdMap

    부작용:
    - target이 없으면 DroneSopUserSdwtChannel row를 생성합니다.
    - 동일 조합의 비활성 mapping은 재활성화합니다.

    오류:
    - ValueError: 필수 입력 누락, line/target 불일치
    - DroneSopTargetMappingDuplicateError: 동일 활성 조합이 이미 존재
    """

    normalized_line_id = _normalize_required_mapping_value(line_id, "lineId")
    normalized_target = _normalize_required_mapping_value(target_user_sdwt_prod, "targetUserSdwtProd")
    normalized_sdwt = _normalize_required_mapping_value(sdwt_prod, "sdwtProd")
    normalized_user_sdwt = _normalize_required_mapping_value(user_sdwt_prod, "userSdwtProd")
    target_source = (
        DroneSopUserSdwtChannel.Sources.AFFILIATION
        if selectors.affiliation_exists_for_user_sdwt_prod(user_sdwt_prod=normalized_target)
        else DroneSopUserSdwtChannel.Sources.CUSTOM
    )

    with transaction.atomic():
        active_duplicate = (
            DroneSopUserSdwtProdMap.objects.select_for_update()
            .filter(
                sdwt_prod__iexact=normalized_sdwt,
                user_sdwt_prod__iexact=normalized_user_sdwt,
                is_active=True,
            )
            .order_by("id")
            .first()
        )
        if active_duplicate is not None:
            raise DroneSopTargetMappingDuplicateError("target mapping already exists")

        mapping = (
            DroneSopUserSdwtProdMap.objects.select_for_update()
            .select_related("target")
            .filter(
                sdwt_prod__iexact=normalized_sdwt,
                user_sdwt_prod__iexact=normalized_user_sdwt,
                target__target_user_sdwt_prod__iexact=normalized_target,
            )
            .order_by("id")
            .first()
        )

        if mapping is not None and mapping.is_active:
            raise DroneSopTargetMappingDuplicateError("target mapping already exists")

        target, _ = ensure_drone_sop_notification_target(
            line_id=normalized_line_id,
            target_user_sdwt_prod=normalized_target,
            actor=actor,
            source=target_source,
        )

        try:
            if mapping is not None:
                mapping.sdwt_prod = normalized_sdwt
                mapping.user_sdwt_prod = normalized_user_sdwt
                mapping.target = target
                mapping.is_active = True
                mapping.save(
                    update_fields=[
                        "sdwt_prod",
                        "user_sdwt_prod",
                        "target",
                        "is_active",
                        "updated_at",
                    ]
                )
                return mapping

            return DroneSopUserSdwtProdMap.objects.create(
                sdwt_prod=normalized_sdwt,
                user_sdwt_prod=normalized_user_sdwt,
                target=target,
                is_active=True,
            )
        except IntegrityError as exc:
            raise DroneSopTargetMappingDuplicateError("target mapping already exists") from exc


__all__ = [
    "DroneSopTargetMappingDuplicateError",
    "create_drone_sop_target_mapping",
]
