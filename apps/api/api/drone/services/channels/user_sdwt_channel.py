# =============================================================================
# 모듈: Drone SOP 채널 설정 서비스
# 주요 함수: upsert_drone_sop_user_sdwt_channel, ensure_drone_sop_notification_target
# 주요 가정: target_user_sdwt_prod 단위로 단일 알림 target을 관리합니다.
# =============================================================================
"""Drone SOP 채널 설정 갱신 서비스 모음."""

from __future__ import annotations

from typing import Any

from django.db import transaction

from ... import selectors
from ...models import DroneSopUserSdwtChannel
from .normalization import UNSET as _UNSET, same_text as _same_text
from .user_sdwt_upsert import (
    apply_user_sdwt_channel_field_updates,
    normalize_user_sdwt_channel_target,
    normalize_user_sdwt_channel_upsert_fields,
)


def upsert_drone_sop_user_sdwt_channel(
    *,
    target_user_sdwt_prod: str,
    line_id: str | None | object = _UNSET,
    source: str | object = _UNSET,
    actor: Any | None = None,
    jira_key: str | None | object = _UNSET,
    chatroom_id: int | None | object = _UNSET,
    jira_template_key: str | None | object = _UNSET,
    mail_template_key: str | None | object = _UNSET,
    messenger_template_key: str | None | object = _UNSET,
    jira_enabled: bool | object = _UNSET,
    messenger_enabled: bool | object = _UNSET,
    mail_enabled: bool | object = _UNSET,
    needtosend_comment_last_at: str | None | object = _UNSET,
    needtosend_ignore_sample_type: bool | object = _UNSET,
    needtosend_enabled: bool | object = _UNSET,
) -> tuple[DroneSopUserSdwtChannel, int]:
    """target_user_sdwt_prod에 대한 알림 target/채널 설정을 생성 또는 갱신합니다.

    입력:
    - target_user_sdwt_prod: 최종 소속 식별자
    - line_id: target 소유 라인(없으면 기존 값을 유지)
    - source: affiliation/custom 중 target 생성 출처
    - actor: target을 생성한 사용자
    - jira_key: Jira 프로젝트 키(없으면 None, 미지정 시 _UNSET)
    - chatroom_id: 채팅룸 ID(없으면 None, 미지정 시 _UNSET)
    - jira_template_key: Jira 템플릿 키(없으면 None, 미지정 시 _UNSET)
    - mail_template_key: 메일 템플릿 키(없으면 None, 미지정 시 _UNSET)
    - messenger_template_key: 메신저 템플릿 키(없으면 None, 미지정 시 _UNSET)
      (미지정이고 기존 messenger_template_key가 비어 있으면 jira_template_key를 기본값으로 동기화)
    - jira_enabled: Jira 채널 활성 여부(미지정 시 _UNSET)
    - messenger_enabled: 메신저 채널 활성 여부(미지정 시 _UNSET)
    - mail_enabled: 메일 채널 활성 여부(미지정 시 _UNSET)
    - needtosend_comment_last_at: 자동 예약 포함 키워드(미지정 시 _UNSET)
    - needtosend_ignore_sample_type: 샘플 타입 제외 규칙 무시 여부(미지정 시 _UNSET)
    - needtosend_enabled: 자동 예약 규칙 활성 여부(미지정 시 _UNSET)

    반환:
    - (DroneSopUserSdwtChannel, int): (갱신된 엔티티, 갱신 여부)

    부작용:
    - DroneSopUserSdwtChannel upsert 수행

    오류:
    - ValueError: 필수 입력 누락 또는 갱신 대상 없음
    """

    # -----------------------------------------------------------------------------
    # 1) 입력 검증
    # -----------------------------------------------------------------------------
    normalized_target = normalize_user_sdwt_channel_target(target_user_sdwt_prod)
    fields = normalize_user_sdwt_channel_upsert_fields(
        line_id=line_id,
        source=source,
        jira_key=jira_key,
        chatroom_id=chatroom_id,
        jira_template_key=jira_template_key,
        mail_template_key=mail_template_key,
        messenger_template_key=messenger_template_key,
        jira_enabled=jira_enabled,
        messenger_enabled=messenger_enabled,
        mail_enabled=mail_enabled,
        needtosend_comment_last_at=needtosend_comment_last_at,
        needtosend_ignore_sample_type=needtosend_ignore_sample_type,
        needtosend_enabled=needtosend_enabled,
    )
    if not fields.has_any_field():
        raise ValueError("at least one field is required")
    if (
        fields.line_id is not _UNSET
        and fields.line_id
        and not selectors.line_id_exists(line_id=fields.line_id)
    ):
        raise ValueError("line_id must be an existing line")

    # -----------------------------------------------------------------------------
    # 2) 행 조회/생성 및 업데이트
    # -----------------------------------------------------------------------------
    with transaction.atomic():
        channel = (
            DroneSopUserSdwtChannel.objects.select_for_update()
            .filter(target_user_sdwt_prod__iexact=normalized_target)
            .order_by("id")
            .first()
        )
        created = channel is None
        if channel is None:
            if fields.line_id is _UNSET:
                raise ValueError("line_id is required for new target")
            channel = DroneSopUserSdwtChannel(target_user_sdwt_prod=normalized_target)
        update_fields: list[str] = []

        if fields.line_id is not _UNSET:
            if not fields.line_id and created:
                raise ValueError("line_id is required for new target")
            if fields.line_id:
                if channel.line_id and not _same_text(channel.line_id, fields.line_id):
                    raise ValueError("targetUserSdwtProd already belongs to another line")
                if channel.line_id != fields.line_id:
                    channel.line_id = fields.line_id
                    update_fields.append("line_id")
        if fields.source is not _UNSET and (created or not channel.source) and channel.source != fields.source:
            channel.source = fields.source
            update_fields.append("source")
        if created and getattr(actor, "is_authenticated", False):
            channel.created_by = actor
            update_fields.append("created_by")

        apply_user_sdwt_channel_field_updates(
            channel=channel,
            fields=fields,
            update_fields=update_fields,
        )
        if not channel.is_active:
            channel.is_active = True
            update_fields.append("is_active")

        if update_fields:
            if created:
                channel.save()
            else:
                channel.save(update_fields=[*update_fields, "updated_at"])
            return channel, 1

        if created:
            channel.save()
            return channel, 1

    return channel, 0


def ensure_drone_sop_notification_target(
    *,
    line_id: str,
    target_user_sdwt_prod: str,
    actor: Any | None = None,
    source: str = DroneSopUserSdwtChannel.Sources.CUSTOM,
) -> tuple[DroneSopUserSdwtChannel, int]:
    """라인별 Drone SOP 알림 target을 생성하거나 기존 target을 반환합니다.

    입력:
    - line_id: target 소유 라인
    - target_user_sdwt_prod: 알림 target 식별자
    - actor: 생성 요청 사용자
    - source: affiliation/custom 중 생성 출처

    반환:
    - (DroneSopUserSdwtChannel, int): (target row, 변경 여부)

    부작용:
    - target이 없으면 DroneSopUserSdwtChannel row를 생성합니다.

    오류:
    - ValueError: line/target/source가 유효하지 않거나 target이 다른 line에 속할 때
    """

    return upsert_drone_sop_user_sdwt_channel(
        target_user_sdwt_prod=target_user_sdwt_prod,
        line_id=line_id,
        source=source,
        actor=actor,
    )


__all__ = [
    "ensure_drone_sop_notification_target",
    "upsert_drone_sop_user_sdwt_channel",
]
