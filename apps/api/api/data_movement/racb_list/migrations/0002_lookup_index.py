# Django 5.2.14가 2026-06-22에 생성

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("racb_list", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="racblist",
            name="eqp_cb_lookup",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.RunSQL(
            "UPDATE racb_list SET eqp_cb_lookup = UPPER(NULLIF(TRIM(eqp_cb), ''))",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AddIndex(
            model_name="racblist",
            index=models.Index(fields=["eqp_cb_lookup", "-update_date"], name="idx_racb_lkp_dt"),
        ),
    ]
