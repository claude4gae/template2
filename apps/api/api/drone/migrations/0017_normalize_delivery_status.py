from django.db import migrations, models
from django.db.models import Q


def normalize_delivery_status(apps, schema_editor):
    """허용되지 않는 delivery status를 성공/실패 상태로 보정합니다."""

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE drone_sop_delivery
            SET
                status = CASE
                    WHEN sent_at IS NOT NULL
                      OR (external_key IS NOT NULL AND external_key <> '')
                    THEN 'success'
                    ELSE 'failed'
                END,
                reason = CASE
                    WHEN sent_at IS NOT NULL
                      OR (external_key IS NOT NULL AND external_key <> '')
                    THEN NULL
                    ELSE 'invalid_status'
                END,
                updated_at = NOW()
            WHERE status NOT IN ('pending', 'success', 'failed', 'disabled')
            """
        )


class Migration(migrations.Migration):
    dependencies = [
        ("drone", "0016_simplify_drone_schema"),
    ]

    operations = [
        migrations.RunPython(normalize_delivery_status, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="dronesopdelivery",
            constraint=models.CheckConstraint(
                condition=Q(status__in=["pending", "success", "failed", "disabled"]),
                name="chk_dro_sop_dlv_sts",
            ),
        ),
    ]
