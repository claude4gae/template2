# Django 5.2.14가 2026-05-29에 생성

import django.db.models.functions.datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="MTkinPrevent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("operator_name", models.TextField(blank=True, null=True)),
                ("tkin_prevent_comment", models.TextField(blank=True, null=True)),
                ("ppid", models.TextField(blank=True, null=True)),
                ("registration_date", models.DateTimeField(blank=True, null=True)),
                ("registration_level", models.TextField(blank=True, null=True)),
                ("fa_object2", models.TextField(blank=True, null=True)),
                ("line_id", models.TextField(blank=True, null=True)),
                ("tkin_prevent_type", models.TextField(blank=True, null=True)),
                ("tkin_restrc_lot_count", models.FloatField(blank=True, null=True)),
                ("last_update_date", models.DateTimeField(blank=True, null=True)),
                ("process_id", models.TextField(blank=True, null=True)),
                ("tkin_lot_count", models.FloatField(blank=True, null=True)),
                ("step_seq", models.TextField(blank=True, null=True)),
                ("metro_lot_count", models.FloatField(blank=True, null=True)),
                ("reticle_id", models.TextField(blank=True, null=True)),
                ("metro_step", models.TextField(blank=True, null=True)),
                ("product_id", models.TextField(blank=True, null=True)),
                ("reg_dept_name", models.TextField(blank=True, null=True)),
                ("update_date", models.DateTimeField(blank=True, null=True)),
                ("eqp_id", models.TextField(blank=True, null=True)),
                ("tkin_prevent_chamber_id", models.TextField(blank=True, null=True)),
                ("schedule_priority", models.TextField(blank=True, null=True)),
                ("photo_comment", models.TextField(blank=True, null=True)),
                ("level2_comment", models.TextField(blank=True, null=True)),
                ("level2_restrc_lot_count", models.FloatField(blank=True, null=True)),
                ("term_intlk_count", models.TextField(blank=True, null=True)),
                ("term_intlk_hour", models.TextField(blank=True, null=True)),
                ("tip_code", models.TextField(blank=True, null=True)),
                ("expo_time", models.TextField(blank=True, null=True)),
                ("check_time", models.FloatField(blank=True, null=True)),
                ("term1_residual_time", models.FloatField(blank=True, null=True)),
                ("check_time2", models.FloatField(blank=True, null=True)),
                ("term2_residual_time", models.FloatField(blank=True, null=True)),
                ("last_tkout_time", models.TextField(blank=True, null=True)),
                ("first_intlk_time", models.TextField(blank=True, null=True)),
                ("tkin_time", models.TextField(blank=True, null=True)),
                ("term_intlk_group_type", models.TextField(blank=True, null=True)),
                ("focus_value", models.TextField(blank=True, null=True)),
                ("prev_rels_level", models.TextField(blank=True, null=True)),
                ("data_chg_type", models.TextField(blank=True, null=True)),
                ("level2_chk_cnt", models.FloatField(blank=True, null=True)),
                ("sample_group_vals", models.TextField(blank=True, null=True)),
                ("auto_tip_rels_type", models.TextField(blank=True, null=True)),
                ("seq_order_no", models.FloatField(blank=True, null=True)),
                ("cd_type", models.TextField(blank=True, null=True)),
                ("rels_group_desc", models.TextField(blank=True, null=True)),
                ("pm_reset_yn", models.TextField(blank=True, null=True)),
                ("rsc_code", models.TextField(blank=True, null=True)),
                ("rsc_chk_mins", models.TextField(blank=True, null=True)),
                ("base_focus_spec", models.TextField(blank=True, null=True)),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_default=django.db.models.functions.datetime.Now(),
                    ),
                ),
            ],
            options={
                "db_table": "m_tkin_prevent",
                "indexes": [models.Index(fields=["line_id"], name="idx_m_tkin_prevent_ln")],
            },
        ),
        migrations.CreateModel(
            name="MTkinPreventLoadJob",
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
                ("replace_values", models.JSONField(blank=True, default=list)),
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
                "db_table": "m_tkin_prevent_load_job",
                "indexes": [
                    models.Index(fields=["status"], name="idx_m_tkin_prv_job_sts"),
                    models.Index(fields=["created_at"], name="idx_m_tkin_prv_job_crt"),
                ],
            },
        ),
    ]
