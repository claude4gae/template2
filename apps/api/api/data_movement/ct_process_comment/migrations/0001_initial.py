# Django 5.2.14가 2026-05-29에 생성

import django.db.models.functions.datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CtProcessComment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("workorder_id", models.CharField(max_length=80)),
                ("line_id", models.TextField(blank=True, null=True)),
                ("process_id", models.TextField(blank=True, null=True)),
                ("process_seq", models.FloatField(blank=True, null=True)),
                ("comment_seq", models.TextField(blank=True, null=True)),
                ("eqp_id", models.TextField(blank=True, null=True)),
                ("freeze_yn", models.TextField(blank=True, null=True)),
                ("contents", models.TextField(blank=True, null=True)),
                ("contents_text", models.TextField(blank=True, null=True)),
                ("create_date", models.DateTimeField(blank=True, null=True)),
                ("create_user", models.TextField(blank=True, null=True)),
                ("update_date", models.DateTimeField(blank=True, null=True)),
                ("update_user", models.TextField(blank=True, null=True)),
                ("use_yn", models.TextField(blank=True, null=True)),
                ("modify_user", models.TextField(blank=True, null=True)),
                ("modify_date", models.DateTimeField(blank=True, null=True)),
                ("pbu_part_key", models.TextField(blank=True, null=True)),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_default=django.db.models.functions.datetime.Now(),
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        db_default=django.db.models.functions.datetime.Now(),
                    ),
                ),
            ],
            options={
                "db_table": "ct_process_comment",
                "indexes": [
                    models.Index(fields=["line_id"], name="idx_ct_prc_cmt_line"),
                    models.Index(fields=["eqp_id"], name="idx_ct_prc_cmt_eqp"),
                    models.Index(fields=["create_date"], name="idx_ct_prc_cmt_crt"),
                ],
                "constraints": [
                    models.UniqueConstraint(fields=["workorder_id"], name="uniq_ct_prc_cmt_wo"),
                ],
            },
        ),
        migrations.CreateModel(
            name="CtProcessCommentLoadJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file_name", models.TextField()),
                ("file_path", models.TextField()),
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
                "db_table": "ct_process_comment_load_job",
                "indexes": [
                    models.Index(fields=["status"], name="idx_ct_prc_cmt_lj_sts"),
                    models.Index(fields=["created_at"], name="idx_ct_prc_cmt_lj_crt"),
                ],
            },
        ),
    ]
