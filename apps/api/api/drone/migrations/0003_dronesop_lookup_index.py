# Django 5.2.14가 2026-06-22에 생성

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("drone", "0002_dronesop_ctttm_urls"),
    ]

    operations = [
        migrations.AddField(
            model_name="dronesop",
            name="eqp_id_lookup",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.RunSQL(
            "UPDATE drone_sop SET eqp_id_lookup = UPPER(NULLIF(TRIM(eqp_id), ''))",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AddIndex(
            model_name="dronesop",
            index=models.Index(fields=["eqp_id_lookup", "-created_at"], name="idx_dro_sop_lkp_crt"),
        ),
    ]
