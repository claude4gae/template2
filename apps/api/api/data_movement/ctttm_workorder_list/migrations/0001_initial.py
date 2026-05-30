# Django 5.2.14가 2026-05-29에 생성

import django.db.models.functions.datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CtttmWorkorderList",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_type", models.CharField(max_length=8)),
                ("workorder_id", models.TextField(blank=True, null=True)),
                ("line_id", models.TextField(blank=True, null=True)),
                ("eqp_id", models.TextField(blank=True, null=True)),
                ("work_type", models.TextField(blank=True, null=True)),
                ("description", models.TextField(blank=True, null=True)),
                ("inprg_date", models.DateTimeField(blank=True, null=True)),
                ("comp_date", models.DateTimeField(blank=True, null=True)),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_default=django.db.models.functions.datetime.Now(),
                    ),
                ),
            ],
            options={
                "db_table": "ctttm_workorder_list",
                "indexes": [
                    models.Index(fields=["source_type"], name="idx_ctttm_wol_src"),
                    models.Index(fields=["line_id"], name="idx_ctttm_wol_line"),
                    models.Index(fields=["eqp_id"], name="idx_ctttm_wol_eqp"),
                ],
            },
        ),
        migrations.CreateModel(
            name="CtttmWorkorderListLoadJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file_name", models.TextField()),
                ("file_path", models.TextField()),
                ("source_type", models.CharField(blank=True, max_length=8, null=True)),
                ("file_timestamp", models.CharField(blank=True, max_length=13, null=True)),
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
                "db_table": "ctttm_workorder_list_load_job",
                "indexes": [
                    models.Index(fields=["source_type"], name="idx_ctttm_wolj_src"),
                    models.Index(fields=["status"], name="idx_ctttm_wolj_sts"),
                    models.Index(fields=["created_at"], name="idx_ctttm_wolj_crt"),
                ],
            },
        ),
    ]
