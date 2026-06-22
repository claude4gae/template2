# Django 5.2.14가 2026-06-22에 생성

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mi_tip_update_hist", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="mitipupdatehist",
            name="eqp_cb_lookup",
            field=models.CharField(blank=True, max_length=65, null=True),
        ),
        migrations.RunSQL(
            "UPDATE mi_tip_update_hist SET eqp_cb_lookup = UPPER(NULLIF(TRIM(eqp_cb), ''))",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AddIndex(
            model_name="mitipupdatehist",
            index=models.Index(fields=["eqp_cb_lookup", "-gpm_update_date"], name="idx_mi_tip_lkp_dt"),
        ),
    ]
