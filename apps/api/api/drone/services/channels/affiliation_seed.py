# =============================================================================
# 모듈: Drone SOP account 소속 기반 초기 설정
# 주요 함수: seed_drone_sop_affiliation_notification_defaults
# 주요 가정: 기존 설정은 덮어쓰지 않고 누락된 row만 생성합니다.
# =============================================================================
"""account 소속 데이터 기반 Drone SOP 알림 초기 설정 서비스입니다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import IntegrityError, transaction

import api.account.selectors as account_selectors

from ...models import (
    DroneSopNeedToSendRule,
    DroneSopTarget,
    DroneSopTargetChannelConfig,
    DroneSopTargetMapping,
    DroneSopTargetRecipient,
)
from .user_sdwt_channel import get_or_create_drone_sop_target_by_name


@dataclass
class DroneSopAffiliationSeedResult:
    """account 소속 기반 Drone SOP 초기 설정 결과입니다."""

    affiliation_targets: int = 0
    targets_created: int = 0
    target_lines_filled: int = 0
    mappings_created: int = 0
    channel_configs_created: int = 0
    needtosend_rules_created: int = 0
    user_recipients_created: int = 0
    external_recipients_created: int = 0
    skipped_existing_mappings: int = 0

    @property
    def recipients_created(self) -> int:
        """생성된 전체 수신인 row 수를 반환합니다."""

        return self.user_recipients_created + self.external_recipients_created

    def as_dict(self) -> dict[str, int]:
        """커맨드 출력에 사용할 dict 형태로 변환합니다."""

        return {
            "affiliation_targets": self.affiliation_targets,
            "targets_created": self.targets_created,
            "target_lines_filled": self.target_lines_filled,
            "mappings_created": self.mappings_created,
            "channel_configs_created": self.channel_configs_created,
            "needtosend_rules_created": self.needtosend_rules_created,
            "user_recipients_created": self.user_recipients_created,
            "external_recipients_created": self.external_recipients_created,
            "recipients_created": self.recipients_created,
            "skipped_existing_mappings": self.skipped_existing_mappings,
        }


def _normalize_text(value: Any) -> str:
    """문자열 값을 공백 제거 기준으로 정규화합니다."""

    return value.strip() if isinstance(value, str) else ""


def _iter_affiliation_targets(*, line_id: str = "") -> list[dict[str, str]]:
    """account_affiliation에서 초기 설정 대상 line/user_sdwt_prod 목록을 조회합니다."""

    normalized_line_id = _normalize_text(line_id)
    rows = account_selectors.list_line_sdwt_pairs()
    if normalized_line_id:
        return [
            row
            for row in rows
            if _normalize_text(row.get("line_id")).casefold() == normalized_line_id.casefold()
        ]
    return rows


def _get_or_create_target_from_affiliation(
    *,
    line_id: str,
    target_user_sdwt_prod: str,
) -> tuple[DroneSopTarget, bool, bool]:
    """account 소속 target을 생성하거나 기존 target의 빈 line_id만 보완합니다."""

    existing = (
        DroneSopTarget.objects.select_for_update()
        .filter(target_user_sdwt_prod__iexact=target_user_sdwt_prod)
        .order_by("id")
        .first()
    )
    if existing is None:
        target = get_or_create_drone_sop_target_by_name(
            target_user_sdwt_prod=target_user_sdwt_prod,
            line_id=line_id,
        )
        return target, True, False

    if not _normalize_text(existing.line_id):
        existing.line_id = line_id
        existing.save(update_fields=["line_id", "updated_at"])
        return existing, False, True
    return existing, False, False


def _ensure_self_mapping(*, target: DroneSopTarget, value: str) -> tuple[bool, bool]:
    """sdwt_prod와 user_sdwt_prod가 같은 self mapping을 없을 때만 생성합니다."""

    existing = (
        DroneSopTargetMapping.objects.select_for_update()
        .filter(sdwt_prod__iexact=value, user_sdwt_prod__iexact=value)
        .order_by("id")
        .first()
    )
    if existing is not None:
        return False, existing.target_id != target.id
    try:
        with transaction.atomic():
            DroneSopTargetMapping.objects.create(
                sdwt_prod=value,
                user_sdwt_prod=value,
                target=target,
            )
            return True, False
    except IntegrityError:
        return False, True


def _ensure_channel_defaults(*, target: DroneSopTarget, template_key: str) -> int:
    """target의 기본 채널 설정을 없는 row에만 생성합니다."""

    specs = [
        (DroneSopTargetChannelConfig.Channels.JIRA, False),
        (DroneSopTargetChannelConfig.Channels.MESSENGER, True),
        (DroneSopTargetChannelConfig.Channels.MAIL, True),
    ]
    created_count = 0
    for channel, enabled in specs:
        _, created = DroneSopTargetChannelConfig.objects.get_or_create(
            target=target,
            channel=channel,
            defaults={
                "enabled": enabled,
                "template_key": template_key,
            },
        )
        created_count += int(created)
    return created_count


def _ensure_needtosend_rule(*, target: DroneSopTarget, comment_keyword: str) -> bool:
    """자동예약 기본 규칙을 없는 row에만 생성합니다."""

    _, created = DroneSopNeedToSendRule.objects.get_or_create(
        target=target,
        defaults={
            "enabled": False,
            "comment_keyword": comment_keyword,
            "ignore_sample_type": False,
        },
    )
    return bool(created)


def _recipient_exists(
    *,
    target: DroneSopTarget,
    channel: str,
    user_id: int | None = None,
    external_knox_id: str = "",
) -> bool:
    """동일 target/channel 수신인 row가 이미 있는지 확인합니다."""

    queryset = DroneSopTargetRecipient.objects.filter(target=target, channel=channel)
    if user_id is not None:
        return queryset.filter(user_id=user_id).exists()
    normalized_external = external_knox_id.strip().lower()
    if not normalized_external:
        return True
    return queryset.filter(external_knox_id=normalized_external).exists()


def _create_recipient_if_missing(
    *,
    target: DroneSopTarget,
    channel: str,
    user_id: int | None = None,
    external_knox_id: str = "",
) -> tuple[int, int]:
    """수신인 row를 없을 때만 생성하고 user/external 생성 카운트를 반환합니다."""

    normalized_external = external_knox_id.strip().lower()
    if user_id is None and not normalized_external:
        return 0, 0
    if _recipient_exists(
        target=target,
        channel=channel,
        user_id=user_id,
        external_knox_id=normalized_external,
    ):
        return 0, 0
    try:
        with transaction.atomic():
            DroneSopTargetRecipient.objects.create(
                target=target,
                channel=channel,
                user_id=user_id,
                external_knox_id="" if user_id is not None else normalized_external,
            )
    except IntegrityError:
        return 0, 0
    return (1, 0) if user_id is not None else (0, 1)


def _seed_channel_recipients(
    *,
    target: DroneSopTarget,
    target_user_sdwt_prod: str,
    channel: str,
    contact_field: str,
) -> tuple[int, int]:
    """account 사용자 pool을 기준으로 특정 채널 수신인을 추가합니다."""

    user_created = 0
    external_created = 0
    recipients = account_selectors.list_active_user_pool(
        user_sdwt_prod=target_user_sdwt_prod,
        contact_field=contact_field,
        include_external_snapshots=True,
        limit=None,
    )
    for recipient in recipients:
        if recipient.get("recipientType") == "external":
            added_user, added_external = _create_recipient_if_missing(
                target=target,
                channel=channel,
                external_knox_id=_normalize_text(recipient.get("externalKnoxId") or recipient.get("knoxId")),
            )
        else:
            user_id = recipient.get("userId")
            added_user, added_external = _create_recipient_if_missing(
                target=target,
                channel=channel,
                user_id=user_id if isinstance(user_id, int) else None,
            )
        user_created += added_user
        external_created += added_external
    return user_created, external_created


def seed_drone_sop_affiliation_notification_defaults(
    *,
    line_id: str = "",
    template_key: str = "common",
    comment_keyword: str = "$SETUP_EQP",
) -> DroneSopAffiliationSeedResult:
    """account_affiliation 기준 Drone SOP 알림 target 기본값을 누락분만 생성합니다."""

    normalized_template_key = _normalize_text(template_key) or "common"
    normalized_comment_keyword = _normalize_text(comment_keyword) or "$SETUP_EQP"
    result = DroneSopAffiliationSeedResult()

    with transaction.atomic():
        for row in _iter_affiliation_targets(line_id=line_id):
            target_user_sdwt_prod = _normalize_text(row.get("user_sdwt_prod"))
            row_line_id = _normalize_text(row.get("line_id"))
            if not target_user_sdwt_prod or not row_line_id:
                continue

            result.affiliation_targets += 1
            target, target_created, line_filled = _get_or_create_target_from_affiliation(
                line_id=row_line_id,
                target_user_sdwt_prod=target_user_sdwt_prod,
            )
            result.targets_created += int(target_created)
            result.target_lines_filled += int(line_filled)

            mapping_created, mapping_skipped = _ensure_self_mapping(
                target=target,
                value=target_user_sdwt_prod,
            )
            result.mappings_created += int(mapping_created)
            result.skipped_existing_mappings += int(mapping_skipped)
            result.channel_configs_created += _ensure_channel_defaults(
                target=target,
                template_key=normalized_template_key,
            )
            result.needtosend_rules_created += int(
                _ensure_needtosend_rule(
                    target=target,
                    comment_keyword=normalized_comment_keyword,
                )
            )

            mail_user_created, mail_external_created = _seed_channel_recipients(
                target=target,
                target_user_sdwt_prod=target_user_sdwt_prod,
                channel=DroneSopTargetRecipient.Channels.MAIL,
                contact_field="email",
            )
            messenger_user_created, messenger_external_created = _seed_channel_recipients(
                target=target,
                target_user_sdwt_prod=target_user_sdwt_prod,
                channel=DroneSopTargetRecipient.Channels.MESSENGER,
                contact_field="knox_id",
            )
            result.user_recipients_created += mail_user_created + messenger_user_created
            result.external_recipients_created += mail_external_created + messenger_external_created

    return result


__all__ = [
    "DroneSopAffiliationSeedResult",
    "seed_drone_sop_affiliation_notification_defaults",
]
