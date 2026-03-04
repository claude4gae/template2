from django.db import migrations
from django.db.models import F, Q


def _backfill_messenger_template_key(apps, schema_editor):  # pragma: no cover
    """기존 채널 행의 messenger_template_key를 jira_template_key로 보정합니다."""

    DroneSopUserSdwtChannel = apps.get_model("drone", "DroneSopUserSdwtChannel")
    DroneSopUserSdwtChannel.objects.filter(
        Q(messenger_template_key__isnull=True) | Q(messenger_template_key=""),
        Q(jira_template_key__isnull=False) & ~Q(jira_template_key=""),
    ).update(messenger_template_key=F("jira_template_key"))


class Migration(migrations.Migration):
    dependencies = [
        ("drone", "0004_dronesop_target_user_sdwt_prod"),
    ]

    operations = [
        migrations.RunPython(_backfill_messenger_template_key, migrations.RunPython.noop),
    ]
