# Django 5.2.14가 2026-06-22에 생성

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mes_line_mapping_info", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="meslinemappinginfo",
            name="gpm_line_name_lookup",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.RunSQL(
            """
            UPDATE mes_line_mapping_info
            SET gpm_line_name_lookup = UPPER(NULLIF(TRIM(gpm_line_name), ''))
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AddIndex(
            model_name="meslinemappinginfo",
            index=models.Index(
                fields=["gpm_line_name_lookup", "gbm_name", "use_yn", "del_yn"],
                name="idx_mes_gpm_flg",
            ),
        ),
        migrations.AddIndex(
            model_name="meslinemappinginfo",
            index=models.Index(
                fields=["msg_line_id", "gbm_name", "use_yn", "del_yn"],
                name="idx_mes_msg_flg",
            ),
        ),
    ]
