# Django 5.2.14가 2026-06-20에 생성

import django.db.models.functions.datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="MesEqpMappingInfo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("eqp_id", models.CharField(blank=True, max_length=40, null=True)),
                ("line_id", models.CharField(blank=True, max_length=40, null=True)),
                ("mos_line_id", models.CharField(blank=True, max_length=40, null=True)),
                ("fdc_line_id", models.CharField(blank=True, max_length=40, null=True)),
                ("gpm_line_name", models.CharField(blank=True, max_length=40, null=True)),
                ("oi_line_name", models.CharField(blank=True, max_length=40, null=True)),
                ("msg_line_id", models.CharField(blank=True, max_length=40, null=True)),
                ("mcs_line_id", models.CharField(blank=True, max_length=40, null=True)),
                ("main_eqp_id", models.CharField(blank=True, max_length=40, null=True)),
                ("chamber_id", models.CharField(blank=True, max_length=40, null=True)),
                ("fdc_eqp_index_no", models.FloatField(blank=True, null=True)),
                ("fdc_unit_index_no", models.FloatField(blank=True, null=True)),
                ("fdc_unit_id", models.CharField(blank=True, max_length=40, null=True)),
                ("fdc_unit_disp_name", models.CharField(blank=True, max_length=40, null=True)),
                ("fdc_eqp_unit_type", models.CharField(blank=True, max_length=100, null=True)),
                ("smdm_eqp_key_no", models.CharField(blank=True, max_length=40, null=True)),
                ("gpm_room_name", models.CharField(blank=True, max_length=40, null=True)),
                ("gpm_eqp_model_name", models.CharField(blank=True, max_length=100, null=True)),
                ("fdc_eqp_model_name", models.CharField(blank=True, max_length=100, null=True)),
                ("fdc_model_name", models.CharField(blank=True, max_length=100, null=True)),
                ("sdwt_name", models.CharField(blank=True, max_length=500, null=True)),
                ("eqp_type", models.CharField(blank=True, max_length=40, null=True)),
                ("insert_date", models.DateTimeField(blank=True, null=True)),
                ("update_date", models.DateTimeField(blank=True, null=True)),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_default=django.db.models.functions.datetime.Now(),
                    ),
                ),
            ],
            options={
                "db_table": "mes_eqp_mapping_info",
                "indexes": [
                    models.Index(fields=["eqp_id"], name="idx_mes_eqp_map_eqp"),
                    models.Index(fields=["line_id"], name="idx_mes_eqp_map_line"),
                ],
            },
        ),
        migrations.CreateModel(
            name="MesEqpMappingInfoLoadJob",
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
                "db_table": "mes_eqp_mapping_info_load_job",
                "indexes": [
                    models.Index(fields=["status"], name="idx_mes_eqp_map_job_sts"),
                    models.Index(fields=["created_at"], name="idx_mes_eqp_map_job_crt"),
                ],
            },
        ),
    ]
