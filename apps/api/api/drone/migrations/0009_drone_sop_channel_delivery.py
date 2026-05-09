import django.db.models.functions.datetime
import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("drone", "0008_remove_dronesop_defect_png_url"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="dronesopusersdwtprodmap",
            name="uniq_dro_sop_sdw_usr_map",
        ),
        migrations.RemoveConstraint(
            model_name="dronesopusersdwtprodmap",
            name="uniq_dro_sop_sdw_map",
        ),
        migrations.RemoveConstraint(
            model_name="dronesopusersdwtprodmap",
            name="uniq_dro_sop_usr_map",
        ),
        migrations.CreateModel(
            name="DroneSopChannelDelivery",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("target_user_sdwt_prod", models.CharField(max_length=64)),
                (
                    "channel",
                    models.CharField(
                        choices=[("jira", "Jira"), ("mail", "Mail"), ("messenger", "Messenger")],
                        max_length=16,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("success", "Success"),
                            ("failed", "Failed"),
                            ("disabled", "Disabled"),
                        ],
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("reason", models.CharField(blank=True, max_length=64, null=True)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, db_default=django.db.models.functions.datetime.Now()),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, db_default=django.db.models.functions.datetime.Now()),
                ),
                (
                    "sop",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="channel_deliveries",
                        to="drone.dronesop",
                    ),
                ),
            ],
            options={
                "db_table": "drone_sop_channel_delivery",
                "indexes": [
                    models.Index(fields=["sop", "channel"], name="idx_dro_sop_chn_dlv_sop"),
                    models.Index(fields=["target_user_sdwt_prod", "channel", "status"], name="idx_dro_sop_chn_dlv_tgt"),
                    models.Index(fields=["channel", "status"], name="idx_dro_sop_chn_dlv_sts"),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("sop", "target_user_sdwt_prod", "channel"),
                        name="uniq_dro_sop_chn_dlv",
                    ),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="dronesopusersdwtprodmap",
            constraint=models.UniqueConstraint(
                fields=("sdwt_prod", "user_sdwt_prod", "target_user_sdwt_prod"),
                condition=(
                    Q(("sdwt_prod__isnull", False))
                    & ~Q(("sdwt_prod", ""))
                    & Q(("user_sdwt_prod__isnull", False))
                    & ~Q(("user_sdwt_prod", ""))
                ),
                name="uniq_dro_sop_sdw_usr_tgt",
            ),
        ),
        migrations.AddConstraint(
            model_name="dronesopusersdwtprodmap",
            constraint=models.UniqueConstraint(
                fields=("sdwt_prod", "target_user_sdwt_prod"),
                condition=(
                    Q(("sdwt_prod__isnull", False))
                    & ~Q(("sdwt_prod", ""))
                    & (Q(("user_sdwt_prod__isnull", True)) | Q(("user_sdwt_prod", "")))
                ),
                name="uniq_dro_sop_sdw_tgt",
            ),
        ),
        migrations.AddConstraint(
            model_name="dronesopusersdwtprodmap",
            constraint=models.UniqueConstraint(
                fields=("user_sdwt_prod", "target_user_sdwt_prod"),
                condition=(
                    Q(("user_sdwt_prod__isnull", False))
                    & ~Q(("user_sdwt_prod", ""))
                    & (Q(("sdwt_prod__isnull", True)) | Q(("sdwt_prod", "")))
                ),
                name="uniq_dro_sop_usr_tgt",
            ),
        ),
    ]
