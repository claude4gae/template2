# Django 5.2.14가 2026-06-22에 생성

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ctttm_workorder_list", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="ctttmworkorderlist",
            name="eqp_id_lookup",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.RunSQL(
            "UPDATE ctttm_workorder_list SET eqp_id_lookup = UPPER(NULLIF(TRIM(eqp_id), ''))",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AddIndex(
            model_name="ctttmworkorderlist",
            index=models.Index(fields=["eqp_id_lookup", "-inprg_date"], name="idx_ctttm_lkp_dt"),
        ),
    ]
