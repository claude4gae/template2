# =============================================================================
# 모듈: Drone SOP 알림 초기 설정
# 주요 함수: seed_drone_sop_notification_defaults_from_rows
# 주요 가정: 기존 알림 설정을 초기화한 뒤 seed row 기준으로 다시 생성합니다.
# =============================================================================
"""외부 row 기반 Drone SOP 알림 초기 설정 서비스입니다."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from django.db import IntegrityError, transaction

import api.account.selectors as account_selectors

from ...models import (
    DroneSOP,
    DroneSopDelivery,
    DroneSopNeedToSendRule,
    DroneSopTarget,
    DroneSopTargetChannelConfig,
    DroneSopTargetDispatch,
    DroneSopTargetMapping,
    DroneSopTargetRecipient,
)
from .user_sdwt_channel import get_or_create_drone_sop_target_by_name


@dataclass
class DroneSopAffiliationSeedResult:
    """Drone SOP 초기 설정 결과입니다."""

    affiliation_targets: int = 0
    targets_created: int = 0
    target_lines_filled: int = 0
    mappings_created: int = 0
    channel_configs_created: int = 0
    needtosend_rules_created: int = 0
    user_recipients_created: int = 0
    external_recipients_created: int = 0
    skipped_existing_mappings: int = 0
    targets_deleted: int = 0
    mappings_deleted: int = 0
    channel_configs_deleted: int = 0
    needtosend_rules_deleted: int = 0
    recipients_deleted: int = 0
    sop_rows_deleted: int = 0
    dispatches_deleted: int = 0
    deliveries_deleted: int = 0

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
            "targets_deleted": self.targets_deleted,
            "mappings_deleted": self.mappings_deleted,
            "channel_configs_deleted": self.channel_configs_deleted,
            "needtosend_rules_deleted": self.needtosend_rules_deleted,
            "recipients_deleted": self.recipients_deleted,
            "sop_rows_deleted": self.sop_rows_deleted,
            "dispatches_deleted": self.dispatches_deleted,
            "deliveries_deleted": self.deliveries_deleted,
        }


def _normalize_text(value: Any) -> str:
    """문자열 값을 공백 제거 기준으로 정규화합니다."""

    return value.strip() if isinstance(value, str) else ""


_CHANNEL_DEFAULTS: dict[str, dict[str, Any]] = {
    DroneSopTargetChannelConfig.Channels.JIRA: {
        "enabled": False,
        "template_key": "common",
        "jira_project_key": None,
        "chatroom_id": None,
        "force_new_chatroom": False,
    },
    DroneSopTargetChannelConfig.Channels.MESSENGER: {
        "enabled": True,
        "template_key": "common",
        "jira_project_key": None,
        "chatroom_id": None,
        "force_new_chatroom": True,
    },
    DroneSopTargetChannelConfig.Channels.MAIL: {
        "enabled": True,
        "template_key": "common",
        "jira_project_key": None,
        "chatroom_id": None,
        "force_new_chatroom": False,
    },
}


def _normalize_bool(value: Any, *, default: bool) -> bool:
    """JSON boolean 값을 정규화하고 값이 없으면 기본값을 반환합니다."""

    return value if isinstance(value, bool) else default


def _normalize_int_or_none(value: Any) -> int | None:
    """양의 정수 또는 None으로 chatroom_id 값을 정규화합니다."""

    if value is None:
        return None
    if isinstance(value, int) and value > 0:
        return value
    return None


def _normalize_seed_target_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """외부 seed row를 공통 내부 형식으로 정규화합니다."""

    normalized_rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        department = _normalize_text(row.get("department"))
        line_id = _normalize_text(row.get("line_id")) or _normalize_text(row.get("line"))
        legacy_user_sdwt_prod = _normalize_text(row.get("user_sdwt_prod"))
        target_user_sdwt_prod = _normalize_text(row.get("target_user_sdwt_prod")) or legacy_user_sdwt_prod
        recipient_user_sdwt_prod = _normalize_text(row.get("recipient_user_sdwt_prod")) or legacy_user_sdwt_prod
        if not recipient_user_sdwt_prod:
            recipient_user_sdwt_prod = target_user_sdwt_prod
        if not line_id or not target_user_sdwt_prod:
            continue
        key = target_user_sdwt_prod.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized_rows.append(
            {
                "department": department,
                "line_id": line_id,
                "target_user_sdwt_prod": target_user_sdwt_prod,
                "recipient_user_sdwt_prod": recipient_user_sdwt_prod,
                "channels": row.get("channels"),
                "mappings": row.get("mappings"),
                "needtosend_rule": row.get("needtosend_rule"),
            }
        )
    return normalized_rows


def _create_seed_target(
    *,
    line_id: str,
    target_user_sdwt_prod: str,
) -> tuple[DroneSopTarget, bool, bool]:
    """seed target을 생성하거나 기존 target의 빈 line_id만 보완합니다."""

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


def _reset_notification_settings() -> dict[str, int]:
    """Drone SOP/발송 이력/알림 설정 테이블을 초기화하고 삭제 카운트를 반환합니다."""

    deliveries_deleted, _ = DroneSopDelivery.objects.all().delete()
    dispatches_deleted, _ = DroneSopTargetDispatch.objects.all().delete()
    sop_rows_deleted, _ = DroneSOP.objects.all().delete()
    recipients_deleted, _ = DroneSopTargetRecipient.objects.all().delete()
    mappings_deleted, _ = DroneSopTargetMapping.objects.all().delete()
    channel_configs_deleted, _ = DroneSopTargetChannelConfig.objects.all().delete()
    needtosend_rules_deleted, _ = DroneSopNeedToSendRule.objects.all().delete()
    targets_deleted, _ = DroneSopTarget.objects.all().delete()
    return {
        "targets_deleted": targets_deleted,
        "mappings_deleted": mappings_deleted,
        "channel_configs_deleted": channel_configs_deleted,
        "needtosend_rules_deleted": needtosend_rules_deleted,
        "recipients_deleted": recipients_deleted,
        "sop_rows_deleted": sop_rows_deleted,
        "dispatches_deleted": dispatches_deleted,
        "deliveries_deleted": deliveries_deleted,
    }


def _normalize_mapping_specs(*, raw_mappings: Any, fallback_value: str) -> list[dict[str, str]]:
    """JSON mapping 목록을 DroneSopTargetMapping 생성 입력으로 정규화합니다."""

    if raw_mappings is None:
        return [{"sdwt_prod": fallback_value, "user_sdwt_prod": fallback_value}]
    if not isinstance(raw_mappings, list):
        raise ValueError("mappings must be a list")

    specs: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for mapping in raw_mappings:
        if not isinstance(mapping, Mapping):
            raise ValueError("mapping entries must be objects")
        sdwt_prod = _normalize_text(mapping.get("sdwt_prod"))
        user_sdwt_prod = _normalize_text(mapping.get("user_sdwt_prod"))
        if not sdwt_prod and not user_sdwt_prod:
            raise ValueError("mapping requires sdwt_prod or user_sdwt_prod")
        key = (sdwt_prod.casefold(), user_sdwt_prod.casefold())
        if key in seen:
            continue
        seen.add(key)
        specs.append({"sdwt_prod": sdwt_prod, "user_sdwt_prod": user_sdwt_prod})
    return specs


def _create_target_mappings(
    *,
    target: DroneSopTarget,
    mapping_specs: list[dict[str, str]],
    global_mapping_owner: dict[tuple[str, str], str],
) -> int:
    """정규화된 mapping 목록을 target에 연결해 생성합니다."""

    created_count = 0
    target_key = target.target_user_sdwt_prod.casefold()
    for mapping in mapping_specs:
        sdwt_prod = mapping["sdwt_prod"]
        user_sdwt_prod = mapping["user_sdwt_prod"]
        mapping_key = (sdwt_prod.casefold(), user_sdwt_prod.casefold())
        owner = global_mapping_owner.get(mapping_key)
        if owner and owner != target_key:
            raise ValueError("duplicate mapping belongs to multiple targets")
        if owner == target_key:
            continue
        global_mapping_owner[mapping_key] = target_key
        DroneSopTargetMapping.objects.create(
            sdwt_prod=sdwt_prod or None,
            user_sdwt_prod=user_sdwt_prod or None,
            target=target,
        )
        created_count += 1
    return created_count


def _normalize_channel_specs(*, raw_channels: Any, default_template_key: str) -> list[dict[str, Any]]:
    """JSON channel 설정을 3개 채널 생성 spec으로 정규화합니다."""

    if raw_channels is None:
        raw_channels = {}
    if not isinstance(raw_channels, Mapping):
        raise ValueError("channels must be an object")

    unknown_channels = set(raw_channels.keys()) - set(_CHANNEL_DEFAULTS.keys())
    if unknown_channels:
        raise ValueError("channels contains unsupported channel")

    specs: list[dict[str, Any]] = []
    for channel, defaults in _CHANNEL_DEFAULTS.items():
        raw_config = raw_channels.get(channel) or {}
        if not isinstance(raw_config, Mapping):
            raise ValueError("channel config must be an object")
        default_template = default_template_key or _normalize_text(defaults.get("template_key"))
        template_key = _normalize_text(raw_config.get("template_key")) or default_template
        specs.append(
            {
                "channel": channel,
                "enabled": _normalize_bool(raw_config.get("enabled"), default=bool(defaults["enabled"])),
                "template_key": template_key,
                "jira_project_key": _normalize_text(raw_config.get("jira_project_key"))
                or defaults.get("jira_project_key"),
                "chatroom_id": _normalize_int_or_none(raw_config.get("chatroom_id")),
                "force_new_chatroom": _normalize_bool(
                    raw_config.get("force_new_chatroom"),
                    default=bool(defaults["force_new_chatroom"]),
                ),
            }
        )
    return specs


def _create_channel_configs(*, target: DroneSopTarget, channel_specs: list[dict[str, Any]]) -> int:
    """정규화된 channel spec으로 target 채널 설정을 생성합니다."""

    created_count = 0
    for spec in channel_specs:
        DroneSopTargetChannelConfig.objects.create(
            target=target,
            channel=spec["channel"],
            enabled=spec["enabled"],
            template_key=spec["template_key"],
            jira_project_key=spec["jira_project_key"],
            chatroom_id=spec["chatroom_id"],
            force_new_chatroom=spec["force_new_chatroom"],
        )
        created_count += 1
    return created_count


def _create_needtosend_rule(*, target: DroneSopTarget, raw_rule: Any, comment_keyword: str) -> bool:
    """JSON needtosend_rule 설정 또는 기본값으로 규칙을 생성합니다."""

    if raw_rule is None:
        raw_rule = {}
    if not isinstance(raw_rule, Mapping):
        raise ValueError("needtosend_rule must be an object")
    DroneSopNeedToSendRule.objects.create(
        target=target,
        enabled=_normalize_bool(raw_rule.get("enabled"), default=False),
        comment_keyword=_normalize_text(raw_rule.get("comment_keyword")) or comment_keyword,
        ignore_sample_type=_normalize_bool(raw_rule.get("ignore_sample_type"), default=False),
    )
    return True


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
    department: str,
    target_user_sdwt_prod: str,
    channel: str,
    contact_field: str,
) -> tuple[int, int]:
    """account 사용자 pool을 기준으로 특정 채널 수신인을 추가합니다."""

    user_created = 0
    external_created = 0
    recipients = account_selectors.list_active_user_pool(
        department=department,
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


def seed_drone_sop_notification_defaults_from_rows(
    *,
    rows: Iterable[Mapping[str, Any]],
    template_key: str = "common",
    comment_keyword: str = "$SETUP_EQP",
) -> DroneSopAffiliationSeedResult:
    """외부 target row 기준 Drone SOP 알림 설정을 초기화 후 생성합니다.

    입력:
    - rows: target/channel/mapping/rule 설정을 담은 dict 목록
    - template_key: 새 채널 설정에 사용할 template_key
    - comment_keyword: 새 자동예약 규칙에 사용할 comment keyword

    반환:
    - DroneSopAffiliationSeedResult: 삭제, 생성 및 skip 카운트

    부작용:
    - 기존 Drone SOP/발송 이력/알림 설정을 삭제하고 `drone_sop_target`, mapping,
      channel config, needtosend rule, recipient row를 생성할 수 있습니다.

    오류:
    - 없음. 필수값이 비어 있는 row는 seed 대상에서 제외합니다.
    """

    normalized_template_key = _normalize_text(template_key) or "common"
    normalized_comment_keyword = _normalize_text(comment_keyword) or "$SETUP_EQP"
    result = DroneSopAffiliationSeedResult()
    seed_rows = _normalize_seed_target_rows(rows)

    with transaction.atomic():
        reset_counts = _reset_notification_settings()
        result.targets_deleted = reset_counts["targets_deleted"]
        result.mappings_deleted = reset_counts["mappings_deleted"]
        result.channel_configs_deleted = reset_counts["channel_configs_deleted"]
        result.needtosend_rules_deleted = reset_counts["needtosend_rules_deleted"]
        result.recipients_deleted = reset_counts["recipients_deleted"]
        result.sop_rows_deleted = reset_counts["sop_rows_deleted"]
        result.dispatches_deleted = reset_counts["dispatches_deleted"]
        result.deliveries_deleted = reset_counts["deliveries_deleted"]

        global_mapping_owner: dict[tuple[str, str], str] = {}
        for row in seed_rows:
            department = _normalize_text(row.get("department"))
            target_user_sdwt_prod = _normalize_text(row.get("target_user_sdwt_prod"))
            recipient_user_sdwt_prod = _normalize_text(row.get("recipient_user_sdwt_prod")) or target_user_sdwt_prod
            row_line_id = _normalize_text(row.get("line_id"))
            if not target_user_sdwt_prod or not row_line_id:
                continue

            result.affiliation_targets += 1
            target, target_created, line_filled = _create_seed_target(
                line_id=row_line_id,
                target_user_sdwt_prod=target_user_sdwt_prod,
            )
            result.targets_created += int(target_created)
            result.target_lines_filled += int(line_filled)

            mapping_specs = _normalize_mapping_specs(
                raw_mappings=row.get("mappings"),
                fallback_value=target_user_sdwt_prod,
            )
            result.mappings_created += _create_target_mappings(
                target=target,
                mapping_specs=mapping_specs,
                global_mapping_owner=global_mapping_owner,
            )
            channel_specs = _normalize_channel_specs(
                raw_channels=row.get("channels"),
                default_template_key=normalized_template_key,
            )
            result.channel_configs_created += _create_channel_configs(target=target, channel_specs=channel_specs)
            result.needtosend_rules_created += int(
                _create_needtosend_rule(
                    target=target,
                    raw_rule=row.get("needtosend_rule"),
                    comment_keyword=normalized_comment_keyword,
                )
            )

            mail_user_created, mail_external_created = _seed_channel_recipients(
                target=target,
                department=department,
                target_user_sdwt_prod=recipient_user_sdwt_prod,
                channel=DroneSopTargetRecipient.Channels.MAIL,
                contact_field="email",
            )
            messenger_user_created, messenger_external_created = _seed_channel_recipients(
                target=target,
                department=department,
                target_user_sdwt_prod=recipient_user_sdwt_prod,
                channel=DroneSopTargetRecipient.Channels.MESSENGER,
                contact_field="knox_id",
            )
            result.user_recipients_created += mail_user_created + messenger_user_created
            result.external_recipients_created += mail_external_created + messenger_external_created

    return result


__all__ = [
    "DroneSopAffiliationSeedResult",
    "seed_drone_sop_notification_defaults_from_rows",
]
