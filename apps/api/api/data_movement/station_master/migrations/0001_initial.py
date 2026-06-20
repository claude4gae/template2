# Django 5.2.14가 2026-06-20에 생성

import django.db.models.functions.datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="StationMaster",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("area", models.CharField(blank=True, max_length=40, null=True)),
                ("station", models.CharField(blank=True, max_length=40, null=True)),
                ("room", models.CharField(blank=True, max_length=3, null=True)),
                ("module", models.CharField(blank=True, max_length=2, null=True)),
                ("st_group", models.CharField(blank=True, max_length=2, null=True)),
                ("machine_id", models.CharField(blank=True, max_length=40, null=True)),
                ("machine_type", models.CharField(blank=True, max_length=20, null=True)),
                ("status", models.CharField(blank=True, max_length=2, null=True)),
                ("station_name", models.CharField(blank=True, max_length=40, null=True)),
                ("ch_class", models.CharField(blank=True, max_length=1, null=True)),
                ("ch_main", models.CharField(blank=True, max_length=40, null=True)),
                ("status_desc", models.CharField(blank=True, max_length=60, null=True)),
                ("bay", models.CharField(blank=True, max_length=8, null=True)),
                ("sdwt_eng", models.CharField(blank=True, max_length=40, null=True)),
                ("sdwt_eng2", models.CharField(blank=True, max_length=40, null=True)),
                ("sdwt_prod", models.CharField(blank=True, max_length=150, null=True)),
                ("del_flag", models.CharField(blank=True, max_length=1, null=True)),
                ("machine_time", models.FloatField(blank=True, null=True)),
                ("sbatch_size", models.FloatField(blank=True, null=True)),
                ("c_flag", models.CharField(blank=True, max_length=1, null=True)),
                ("c_run", models.FloatField(blank=True, null=True)),
                ("c_idle", models.FloatField(blank=True, null=True)),
                ("c_idle_rev", models.FloatField(blank=True, null=True)),
                ("da_reason", models.CharField(blank=True, max_length=2, null=True)),
                ("da_date", models.CharField(blank=True, max_length=8, null=True)),
                ("zone", models.CharField(blank=True, max_length=40, null=True)),
                ("block", models.CharField(blank=True, max_length=40, null=True)),
                ("no_del_flag", models.CharField(blank=True, max_length=1, null=True)),
                ("endfab_flag", models.CharField(blank=True, max_length=1, null=True)),
                ("mfab_flag", models.CharField(blank=True, max_length=40, null=True)),
                ("port_cnt", models.FloatField(blank=True, null=True)),
                ("da_reason2", models.CharField(blank=True, max_length=2, null=True)),
                ("oht", models.CharField(blank=True, max_length=1, null=True)),
                ("metro_grp", models.CharField(blank=True, max_length=10, null=True)),
                ("prc_group", models.CharField(blank=True, max_length=50, null=True)),
                ("scanner", models.CharField(blank=True, max_length=40, null=True)),
                ("amhs", models.CharField(blank=True, max_length=2, null=True)),
                ("chm_type", models.CharField(blank=True, max_length=20, null=True)),
                ("fc_step", models.CharField(blank=True, max_length=1, null=True)),
                ("close_day", models.CharField(blank=True, max_length=8, null=True)),
                ("close_shift", models.CharField(blank=True, max_length=1, null=True)),
                ("ad_flag", models.CharField(blank=True, max_length=1, null=True)),
                ("en_reason", models.CharField(blank=True, max_length=2, null=True)),
                ("dv_flag", models.CharField(blank=True, max_length=1, null=True)),
                ("ed_reason", models.CharField(blank=True, max_length=2, null=True)),
                ("in_line", models.CharField(blank=True, max_length=40, null=True)),
                ("floor_line_id", models.CharField(blank=True, max_length=40, null=True)),
                ("index_area", models.CharField(blank=True, max_length=10, null=True)),
                ("dv_date", models.CharField(blank=True, max_length=8, null=True)),
                ("purge_yn", models.CharField(blank=True, max_length=1, null=True)),
                ("purge_target_yn", models.CharField(blank=True, max_length=1, null=True)),
                ("addr_book_id", models.CharField(blank=True, max_length=50, null=True)),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_default=django.db.models.functions.datetime.Now(),
                    ),
                ),
            ],
            options={
                "db_table": "station_master",
                "indexes": [
                    models.Index(fields=["station"], name="idx_station_master_station"),
                    models.Index(fields=["machine_id"], name="idx_station_master_mch"),
                ],
            },
        ),
        migrations.CreateModel(
            name="StationMasterLoadJob",
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
                "db_table": "station_master_load_job",
                "indexes": [
                    models.Index(fields=["status"], name="idx_station_mst_job_sts"),
                    models.Index(fields=["created_at"], name="idx_station_mst_job_crt"),
                ],
            },
        ),
    ]
