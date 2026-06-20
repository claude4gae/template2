# Django 5.2.14가 2026-06-20에 생성

import django.db.models.functions.datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="MesLineMappingInfo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("seq_no", models.FloatField(blank=True, null=True)),
                ("line_id", models.CharField(blank=True, max_length=40, null=True)),
                ("mos_line_id", models.CharField(blank=True, max_length=40, null=True)),
                ("fdc_line_id", models.CharField(blank=True, max_length=40, null=True)),
                ("gpm_line_name", models.TextField(blank=True, null=True)),
                ("oi_line_name", models.CharField(blank=True, max_length=40, null=True)),
                ("msg_line_id", models.CharField(blank=True, max_length=40, null=True)),
                ("mcs_line_id", models.CharField(blank=True, max_length=40, null=True)),
                ("line_full_name", models.CharField(blank=True, max_length=100, null=True)),
                ("line_abbr_name", models.CharField(blank=True, max_length=100, null=True)),
                ("gbm_name", models.CharField(blank=True, max_length=40, null=True)),
                ("site_id", models.CharField(blank=True, max_length=40, null=True)),
                ("district_name", models.CharField(blank=True, max_length=40, null=True)),
                ("inch_vals", models.CharField(blank=True, max_length=40, null=True)),
                ("area_class_type", models.CharField(blank=True, max_length=50, null=True)),
                ("fab_type", models.CharField(blank=True, max_length=40, null=True)),
                ("cdc_user_id", models.CharField(blank=True, max_length=40, null=True)),
                ("fdc_db_user_id", models.CharField(blank=True, max_length=50, null=True)),
                ("mos_eaihub_line_id", models.CharField(blank=True, max_length=40, null=True)),
                ("mos_db_line_name", models.CharField(blank=True, max_length=40, null=True)),
                ("sort_seq", models.FloatField(blank=True, null=True)),
                ("use_yn", models.CharField(blank=True, max_length=1, null=True)),
                ("del_yn", models.CharField(blank=True, max_length=1, null=True)),
                ("create_date", models.DateTimeField(blank=True, null=True)),
                ("create_user_id", models.CharField(blank=True, max_length=40, null=True)),
                ("update_date", models.DateTimeField(blank=True, null=True)),
                ("update_user_id", models.CharField(blank=True, max_length=40, null=True)),
                ("rms_line_id", models.CharField(blank=True, max_length=40, null=True)),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_default=django.db.models.functions.datetime.Now(),
                    ),
                ),
            ],
            options={
                "db_table": "mes_line_mapping_info",
                "indexes": [
                    models.Index(fields=["line_id"], name="idx_mes_line_map_line"),
                    models.Index(fields=["msg_line_id"], name="idx_mes_line_map_msg"),
                    models.Index(fields=["gpm_line_name"], name="idx_mes_line_map_gpm"),
                    models.Index(fields=["gbm_name", "use_yn", "del_yn"], name="idx_mes_line_map_flg"),
                ],
            },
        ),
        migrations.CreateModel(
            name="MesLineMappingInfoLoadJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file_name", models.TextField()),
                ("file_path", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("running", "Running"),
                            ("success", "Success"),
                            ("failed", "Failed"),
                            ("dry_run", "Dry run"),
                        ],
                        default="running",
                        max_length=16,
                    ),
                ),
                ("row_count", models.PositiveIntegerField(blank=True, null=True)),
                ("error_message", models.TextField(blank=True, null=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_default=django.db.models.functions.datetime.Now(),
                    ),
                ),
            ],
            options={
                "db_table": "mes_line_mapping_info_load_job",
                "indexes": [
                    models.Index(fields=["status"], name="idx_mes_line_map_job_sts"),
                    models.Index(fields=["created_at"], name="idx_mes_line_map_job_crt"),
                ],
            },
        ),
    ]
