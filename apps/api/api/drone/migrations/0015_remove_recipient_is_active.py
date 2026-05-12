from django.db import migrations


def delete_inactive_recipient_rows(apps, schema_editor):
    """컬럼 제거 전 비활성 수신인 매핑을 삭제합니다."""

    DroneSopTargetRecipient = apps.get_model("drone", "DroneSopTargetRecipient")
    DroneSopTargetRecipient.objects.filter(is_active=False).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("drone", "0014_global_active_target_mapping_unique"),
    ]

    operations = [
        migrations.RunPython(delete_inactive_recipient_rows, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="dronesoptargetrecipient",
            name="is_active",
        ),
    ]
