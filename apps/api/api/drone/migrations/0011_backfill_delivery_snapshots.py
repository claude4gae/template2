from django.db import migrations
from django.db.models import Exists, OuterRef, Q


CHANNELS = ("jira", "messenger", "mail")
SEND_FIELD_BY_CHANNEL = {
    "jira": "send_jira",
    "messenger": "send_messenger",
    "mail": "send_mail",
}
REASON_FIELD_BY_CHANNEL = {
    "jira": "jira_reason",
    "messenger": "messenger_reason",
    "mail": "mail_reason",
}


def normalize_value(value):
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def lookup_key(value):
    cleaned = normalize_value(value)
    return cleaned.casefold() if cleaned else None


def append_unique(targets, target):
    target_key = lookup_key(target)
    if not target_key:
        return
    if any(lookup_key(existing) == target_key for existing in targets):
        return
    targets.append(str(target).strip())


def build_mapping_index(DroneSopUserSdwtProdMap):
    pair_map = {}
    sdwt_only_map = {}
    user_only_map = {}
    rows = DroneSopUserSdwtProdMap.objects.filter(is_active=True).values(
        "sdwt_prod",
        "user_sdwt_prod",
        "target_user_sdwt_prod",
    )
    for row in rows:
        sdwt = normalize_value(row.get("sdwt_prod"))
        user = normalize_value(row.get("user_sdwt_prod"))
        target = normalize_value(row.get("target_user_sdwt_prod"))
        if not target:
            continue
        sdwt_key = lookup_key(sdwt)
        user_key = lookup_key(user)
        if sdwt_key and user_key:
            append_unique(pair_map.setdefault((sdwt_key, user_key), []), target)
        elif sdwt_key:
            append_unique(sdwt_only_map.setdefault(sdwt_key, []), target)
        elif user_key:
            append_unique(user_only_map.setdefault(user_key, []), target)
    return pair_map, sdwt_only_map, user_only_map


def resolve_targets(row, mapping_index):
    pair_map, sdwt_only_map, user_only_map = mapping_index
    sdwt_key = lookup_key(row.sdwt_prod)
    user_key = lookup_key(row.user_sdwt_prod)
    targets = []
    if sdwt_key and user_key:
        targets = pair_map.get((sdwt_key, user_key), [])
        if targets:
            return targets
    if sdwt_key:
        targets = sdwt_only_map.get(sdwt_key, [])
        if targets:
            return targets
    if user_key:
        targets = user_only_map.get(user_key, [])
        if targets:
            return targets
    legacy_target = normalize_value(row.target_user_sdwt_prod)
    return [legacy_target] if legacy_target else []


def delivery_status_for_channel(row, channel):
    send_field = SEND_FIELD_BY_CHANNEL[channel]
    reason_field = REASON_FIELD_BY_CHANNEL[channel]
    reason = normalize_value(getattr(row, reason_field, None))
    try:
        send_value = int(getattr(row, send_field, 0) or 0)
    except (TypeError, ValueError):
        send_value = 0

    if reason == "disabled_by_policy":
        return "disabled", reason
    if send_value > 0:
        return "success", None
    if send_value < 0:
        return "failed", reason or "send_failed"
    return "pending", None


def delivery_extra_for_channel(row, channel, status):
    external_key = None
    sent_at = None
    if status == "success":
        sent_at = getattr(row, "informed_at", None)
        if channel == "jira":
            external_key = normalize_value(getattr(row, "jira_key", None))
    return external_key, sent_at


def backfill_delivery_snapshots(apps, schema_editor):
    DroneSOP = apps.get_model("drone", "DroneSOP")
    DroneSopChannelDelivery = apps.get_model("drone", "DroneSopChannelDelivery")
    DroneSopUserSdwtProdMap = apps.get_model("drone", "DroneSopUserSdwtProdMap")

    existing_delivery = DroneSopChannelDelivery.objects.filter(sop_id=OuterRef("pk"))
    queryset = (
        DroneSOP.objects.annotate(has_delivery=Exists(existing_delivery))
        .filter(has_delivery=False)
        .filter(Q(needtosend=1, status="COMPLETE") | Q(instant_inform=1))
        .order_by("id")
    )
    mapping_index = build_mapping_index(DroneSopUserSdwtProdMap)

    buffer = []
    for sop in queryset.iterator(chunk_size=1000):
        targets = resolve_targets(sop, mapping_index)
        if not targets:
            continue
        for target in targets:
            for channel in CHANNELS:
                status, reason = delivery_status_for_channel(sop, channel)
                external_key, sent_at = delivery_extra_for_channel(sop, channel, status)
                buffer.append(
                    DroneSopChannelDelivery(
                        sop_id=sop.id,
                        target_user_sdwt_prod=target,
                        channel=channel,
                        status=status,
                        reason=reason,
                        external_key=external_key,
                        sent_at=sent_at,
                    )
                )
        if len(buffer) >= 3000:
            DroneSopChannelDelivery.objects.bulk_create(buffer, ignore_conflicts=True)
            buffer = []
    if buffer:
        DroneSopChannelDelivery.objects.bulk_create(buffer, ignore_conflicts=True)


class Migration(migrations.Migration):
    dependencies = [
        ("drone", "0010_merge_needtosend_rule_into_channel"),
    ]

    operations = [
        migrations.RunPython(backfill_delivery_snapshots, migrations.RunPython.noop),
    ]
