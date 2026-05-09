from django.db import migrations, models


def merge_needtosend_rules(apps, schema_editor):
    DroneSopNeedToSendRule = apps.get_model("drone", "DroneSopNeedToSendRule")
    DroneSopUserSdwtChannel = apps.get_model("drone", "DroneSopUserSdwtChannel")

    for rule in DroneSopNeedToSendRule.objects.order_by("id").iterator(chunk_size=1000):
        target = str(rule.target_user_sdwt_prod or "").strip()
        if not target:
            continue
        channel, _ = DroneSopUserSdwtChannel.objects.get_or_create(
            target_user_sdwt_prod=target,
            defaults={
                "line_id": "",
                "source": "custom",
                "needtosend_comment_last_at": str(rule.comment_last_at or "").strip() or None,
                "needtosend_ignore_sample_type": bool(rule.ignore_sample_type),
                "needtosend_enabled": bool(rule.is_active),
                "is_active": True,
            },
        )
        DroneSopUserSdwtChannel.objects.filter(id=channel.id).update(
            needtosend_comment_last_at=str(rule.comment_last_at or "").strip() or None,
            needtosend_ignore_sample_type=bool(rule.ignore_sample_type),
            needtosend_enabled=bool(rule.is_active),
        )


class Migration(migrations.Migration):
    dependencies = [
        ("drone", "0009_drone_sop_channel_delivery"),
    ]

    operations = [
        migrations.AddField(
            model_name="dronesopchanneldelivery",
            name="external_key",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="dronesopusersdwtchannel",
            name="needtosend_comment_last_at",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddField(
            model_name="dronesopusersdwtchannel",
            name="needtosend_ignore_sample_type",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="dronesopusersdwtchannel",
            name="needtosend_enabled",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(merge_needtosend_rules, migrations.RunPython.noop),
        migrations.DeleteModel(
            name="DroneSopNeedToSendRule",
        ),
    ]
