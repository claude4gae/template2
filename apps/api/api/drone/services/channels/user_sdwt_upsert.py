"""Drone SOP 사용자 SDWT 채널 upsert 입력 helper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...models import DroneSopTarget
from .normalization import (
    UNSET as _UNSET,
    normalize_optional_template_key,
    normalize_optional_text,
    validate_optional_chatroom_id,
    validate_optional_str,
)


@dataclass(frozen=True)
class UserSdwtChannelUpsertFields:
    """정규화된 Drone SOP 채널 upsert 필드 묶음."""

    line_id: str | object
    jira_key: str | None | object
    chatroom_id: int | None | object
    jira_template_key: str | None | object
    mail_template_key: str | None | object
    messenger_template_key: str | None | object
    jira_enabled: bool | object
    messenger_enabled: bool | object
    mail_enabled: bool | object
    needtosend_comment_last_at: str | None | object
    needtosend_ignore_sample_type: bool | object
    needtosend_enabled: bool | object

    def has_any_field(self) -> bool:
        """하나 이상의 갱신 필드가 지정되었는지 확인합니다."""

        return any(
            value is not _UNSET
            for value in (
                self.line_id,
                self.jira_key,
                self.chatroom_id,
                self.jira_template_key,
                self.mail_template_key,
                self.messenger_template_key,
                self.jira_enabled,
                self.messenger_enabled,
                self.mail_enabled,
                self.needtosend_comment_last_at,
                self.needtosend_ignore_sample_type,
                self.needtosend_enabled,
            )
        )


def normalize_user_sdwt_channel_target(value: Any) -> str:
    """target_user_sdwt_prod 필수 입력을 검증하고 공백을 제거합니다."""

    if not isinstance(value, str) or not value.strip():
        raise ValueError("target_user_sdwt_prod is required")
    return value.strip()


def _validate_optional_bool(value: object, field_name: str) -> None:
    """선택 bool 필드가 bool인지 검증합니다."""

    if value is not _UNSET and not isinstance(value, bool):
        raise ValueError(f"{field_name} must be bool")


def normalize_user_sdwt_channel_upsert_fields(
    *,
    line_id: Any,
    jira_key: str | None | object,
    chatroom_id: int | None | object,
    jira_template_key: str | None | object,
    mail_template_key: str | None | object,
    messenger_template_key: str | None | object,
    jira_enabled: bool | object,
    messenger_enabled: bool | object,
    mail_enabled: bool | object,
    needtosend_comment_last_at: str | None | object,
    needtosend_ignore_sample_type: bool | object,
    needtosend_enabled: bool | object,
) -> UserSdwtChannelUpsertFields:
    """채널 upsert 입력 필드를 검증하고 저장용 값으로 정규화합니다."""

    validate_optional_str(jira_key, "jira_key")
    validate_optional_chatroom_id(chatroom_id)
    validate_optional_str(jira_template_key, "jira_template_key")
    validate_optional_str(mail_template_key, "mail_template_key")
    validate_optional_str(messenger_template_key, "messenger_template_key")
    validate_optional_str(needtosend_comment_last_at, "needtosend_comment_last_at")
    _validate_optional_bool(jira_enabled, "jira_enabled")
    _validate_optional_bool(messenger_enabled, "messenger_enabled")
    _validate_optional_bool(mail_enabled, "mail_enabled")
    _validate_optional_bool(needtosend_ignore_sample_type, "needtosend_ignore_sample_type")
    _validate_optional_bool(needtosend_enabled, "needtosend_enabled")

    return UserSdwtChannelUpsertFields(
        line_id=normalize_optional_text(line_id) if line_id is not _UNSET else _UNSET,
        jira_key=jira_key,
        chatroom_id=chatroom_id,
        jira_template_key=normalize_optional_template_key(jira_template_key),
        mail_template_key=normalize_optional_template_key(mail_template_key),
        messenger_template_key=normalize_optional_template_key(messenger_template_key),
        jira_enabled=jira_enabled,
        messenger_enabled=messenger_enabled,
        mail_enabled=mail_enabled,
        needtosend_comment_last_at=normalize_optional_template_key(needtosend_comment_last_at),
        needtosend_ignore_sample_type=needtosend_ignore_sample_type,
        needtosend_enabled=needtosend_enabled,
    )


def set_channel_field_if_changed(
    *,
    channel: DroneSopTarget,
    update_fields: list[str],
    field_name: str,
    value: Any,
) -> None:
    """지정 필드가 변경된 경우 모델 값과 update_fields를 갱신합니다."""

    if value is _UNSET:
        return
    if getattr(channel, field_name) != value:
        setattr(channel, field_name, value)
        update_fields.append(field_name)


def apply_user_sdwt_channel_field_updates(
    *,
    channel: DroneSopTarget,
    fields: UserSdwtChannelUpsertFields,
    update_fields: list[str],
) -> None:
    """정규화된 upsert 필드를 channel 모델에 반영합니다."""

    field_values = (
        ("jira_key", fields.jira_key),
        ("chatroom_id", fields.chatroom_id),
        ("jira_template_key", fields.jira_template_key),
        ("mail_template_key", fields.mail_template_key),
    )
    for field_name, value in field_values:
        set_channel_field_if_changed(
            channel=channel,
            update_fields=update_fields,
            field_name=field_name,
            value=value,
        )

    resolved_messenger_template_key = fields.messenger_template_key
    if (
        resolved_messenger_template_key is _UNSET
        and fields.jira_template_key is not _UNSET
        and not channel.messenger_template_key
    ):
        resolved_messenger_template_key = fields.jira_template_key
    set_channel_field_if_changed(
        channel=channel,
        update_fields=update_fields,
        field_name="messenger_template_key",
        value=resolved_messenger_template_key,
    )

    rule_field_values = (
        ("jira_enabled", fields.jira_enabled),
        ("messenger_enabled", fields.messenger_enabled),
        ("mail_enabled", fields.mail_enabled),
        ("needtosend_comment_last_at", fields.needtosend_comment_last_at),
        ("needtosend_ignore_sample_type", fields.needtosend_ignore_sample_type),
        ("needtosend_enabled", fields.needtosend_enabled),
    )
    for field_name, value in rule_field_values:
        set_channel_field_if_changed(
            channel=channel,
            update_fields=update_fields,
            field_name=field_name,
            value=value,
        )


__all__ = [
    "UserSdwtChannelUpsertFields",
    "apply_user_sdwt_channel_field_updates",
    "normalize_user_sdwt_channel_target",
    "normalize_user_sdwt_channel_upsert_fields",
    "set_channel_field_if_changed",
]
