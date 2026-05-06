import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def _normalize_text(value):  # pragma: no cover
    """문자열 값을 공백 제거 기준으로 정규화합니다."""

    return value.strip() if isinstance(value, str) else ""


def _backfill_notification_target_scope(apps, schema_editor):  # pragma: no cover
    """기존 채널 설정에 line_id/source 스코프를 채웁니다."""

    Affiliation = apps.get_model("account", "Affiliation")
    DroneSOP = apps.get_model("drone", "DroneSOP")
    DroneSopUserSdwtChannel = apps.get_model("drone", "DroneSopUserSdwtChannel")

    line_cache = {}
    affiliation_cache = {}

    def get_sop_line_id(target_user_sdwt_prod):
        """Drone SOP 데이터에서 target의 대표 line_id를 조회합니다."""

        normalized_target = _normalize_text(target_user_sdwt_prod)
        lookup_key = normalized_target.lower()
        if lookup_key in line_cache:
            return line_cache[lookup_key]

        line_id = (
            DroneSOP.objects.filter(target_user_sdwt_prod__iexact=normalized_target)
            .exclude(line_id__isnull=True)
            .exclude(line_id__exact="")
            .values_list("line_id", flat=True)
            .order_by("line_id")
            .first()
        )
        line_cache[lookup_key] = _normalize_text(line_id)
        return line_cache[lookup_key]

    def get_affiliation_line_id(target_user_sdwt_prod):
        """account_affiliation에서 target과 같은 user_sdwt_prod의 line_id를 조회합니다."""

        normalized_target = _normalize_text(target_user_sdwt_prod)
        lookup_key = normalized_target.lower()
        if lookup_key in affiliation_cache:
            return affiliation_cache[lookup_key]

        line_id = (
            Affiliation.objects.filter(user_sdwt_prod__iexact=normalized_target)
            .exclude(line__isnull=True)
            .exclude(line__exact="")
            .values_list("line", flat=True)
            .order_by("line")
            .first()
        )
        affiliation_cache[lookup_key] = _normalize_text(line_id)
        return affiliation_cache[lookup_key]

    for target in DroneSopUserSdwtChannel.objects.order_by("id").iterator(chunk_size=1000):
        target_value = _normalize_text(target.target_user_sdwt_prod)
        if not target_value:
            continue

        sop_line_id = get_sop_line_id(target_value)
        affiliation_line_id = get_affiliation_line_id(target_value)
        resolved_line_id = sop_line_id or affiliation_line_id
        resolved_source = "affiliation" if affiliation_line_id else "custom"

        update_fields = []
        if resolved_line_id and target.line_id != resolved_line_id:
            target.line_id = resolved_line_id
            update_fields.append("line_id")
        if target.source != resolved_source:
            target.source = resolved_source
            update_fields.append("source")
        if update_fields:
            target.save(update_fields=update_fields)


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("account", "0001_initial"),
        ("drone", "0006_drone_sop_channel_recipient"),
    ]

    operations = [
        migrations.AddField(
            model_name="dronesopusersdwtchannel",
            name="line_id",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
        migrations.AddField(
            model_name="dronesopusersdwtchannel",
            name="source",
            field=models.CharField(
                choices=[("affiliation", "Affiliation"), ("custom", "Custom")],
                default="custom",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="dronesopusersdwtchannel",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_drone_sop_notification_targets",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddIndex(
            model_name="dronesopusersdwtchannel",
            index=models.Index(fields=["line_id"], name="idx_dro_sop_usr_chn_ln"),
        ),
        migrations.RunPython(_backfill_notification_target_scope, migrations.RunPython.noop),
    ]
