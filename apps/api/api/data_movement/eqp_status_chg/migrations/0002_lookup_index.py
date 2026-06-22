# Django 5.2.14가 2026-06-22에 생성

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("eqp_status_chg", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="eqpstatuschg",
            name="eqp_cb_lookup",
            field=models.CharField(blank=True, max_length=41, null=True),
        ),
        migrations.RunSQL(
            "UPDATE eqp_status_chg SET eqp_cb_lookup = UPPER(NULLIF(TRIM(eqp_cb), ''))",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AddIndex(
            model_name="eqpstatuschg",
            index=models.Index(fields=["eqp_cb_lookup", "-chg_time"], name="idx_eqp_sts_lkp_tm"),
        ),
    ]
