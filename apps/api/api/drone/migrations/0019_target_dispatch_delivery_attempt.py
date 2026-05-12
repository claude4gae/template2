from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.functions


TARGET_MISSING_CODE = "__TARGET_MISSING__"


def create_dispatches_for_existing_deliveries(apps, schema_editor):
    """기존 delivery row에 대응하는 target dispatch를 생성합니다."""

    DroneSOP = apps.get_model("drone", "DroneSOP")
    DroneSopTarget = apps.get_model("drone", "DroneSopTarget")
    DroneSopTargetDispatch = apps.get_model("drone", "DroneSopTargetDispatch")
    DroneSopDelivery = apps.get_model("drone", "DroneSopDelivery")

    target_by_code = {
        str(target.target_user_sdwt_prod or "").casefold(): target
        for target in DroneSopTarget.objects.all()
        if str(target.target_user_sdwt_prod or "").strip()
    }
    sop_by_id = {sop.id: sop for sop in DroneSOP.objects.all()}

    for delivery in DroneSopDelivery.objects.all().order_by("id"):
        sop = sop_by_id.get(delivery.sop_id)
        if sop is None:
            continue
        target_code = str(getattr(sop, "target_user_sdwt_prod", "") or "").strip() or TARGET_MISSING_CODE
        target = target_by_code.get(target_code.casefold())
        dispatch, _ = DroneSopTargetDispatch.objects.get_or_create(
            sop_id=sop.id,
            target_code_snapshot=target_code,
            defaults={
                "target_id": target.id if target else None,
                "target_display_snapshot": target_code,
                "resolution_status": "resolved" if target_code != TARGET_MISSING_CODE else "target_missing",
                "dispatch_type": "auto",
                "status": "pending",
            },
        )
        delivery.dispatch_id = dispatch.id
        delivery.save(update_fields=["dispatch"])


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("drone", "0018_dronesopdelivery_sent_comment"),
    ]

    operations = [
        migrations.CreateModel(
            name="DroneSopTargetDispatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("target_code_snapshot", models.CharField(max_length=64)),
                ("target_display_snapshot", models.CharField(blank=True, max_length=128, null=True)),
                ("resolution_status", models.CharField(default="resolved", max_length=32)),
                (
                    "dispatch_type",
                    models.CharField(
                        choices=[
                            ("auto", "Auto"),
                            ("instant", "Instant"),
                            ("manual", "Manual"),
                            ("retry", "Retry"),
                        ],
                        default="auto",
                        max_length=16,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("dispatching", "Dispatching"),
                            ("success", "Success"),
                            ("partial_failed", "Partial failed"),
                            ("failed", "Failed"),
                            ("disabled", "Disabled"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="pending",
                        max_length=24,
                    ),
                ),
                ("comment_override", models.TextField(blank=True, null=True)),
                ("requested_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_default=django.db.models.functions.Now())),
                ("updated_at", models.DateTimeField(auto_now=True, db_default=django.db.models.functions.Now())),
                (
                    "requested_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="drone_sop_dispatch_requests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "sop",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="target_dispatches",
                        to="drone.dronesop",
                    ),
                ),
                (
                    "target",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="sop_dispatches",
                        to="drone.dronesoptarget",
                    ),
                ),
            ],
            options={
                "db_table": "drone_sop_target_dispatch",
            },
        ),
        migrations.AddField(
            model_name="dronesopdelivery",
            name="dispatch",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="deliveries",
                to="drone.dronesoptargetdispatch",
            ),
        ),
        migrations.AddField(
            model_name="dronesopdelivery",
            name="attempt_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="dronesopdelivery",
            name="template_key_snapshot",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="dronesopdelivery",
            name="channel_config_snapshot",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dronesopdelivery",
            name="recipient_snapshot",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.RunPython(create_dispatches_for_existing_deliveries, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="dronesopdelivery",
            name="dispatch",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="deliveries",
                to="drone.dronesoptargetdispatch",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="dronesopdelivery",
            name="uniq_dro_sop_delivery",
        ),
        migrations.RemoveConstraint(
            model_name="dronesopdelivery",
            name="chk_dro_sop_dlv_sts",
        ),
        migrations.AlterField(
            model_name="dronesopdelivery",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("sending", "Sending"),
                    ("success", "Success"),
                    ("failed", "Failed"),
                    ("disabled", "Disabled"),
                    ("cancelled", "Cancelled"),
                ],
                default="pending",
                max_length=16,
            ),
        ),
        migrations.AddConstraint(
            model_name="dronesoptargetdispatch",
            constraint=models.UniqueConstraint(
                fields=("sop", "target_code_snapshot"),
                name="uniq_dro_sop_tgt_dsp",
            ),
        ),
        migrations.AddConstraint(
            model_name="dronesoptargetdispatch",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("status__in", ["pending", "dispatching", "success", "partial_failed", "failed", "disabled", "cancelled"])
                ),
                name="chk_dro_sop_tgt_dsp_st",
            ),
        ),
        migrations.AddConstraint(
            model_name="dronesopdelivery",
            constraint=models.UniqueConstraint(
                fields=("dispatch", "channel"),
                name="uniq_dro_sop_dlv_dsp_ch",
            ),
        ),
        migrations.AddConstraint(
            model_name="dronesopdelivery",
            constraint=models.CheckConstraint(
                condition=models.Q(("status__in", ["pending", "sending", "success", "failed", "disabled", "cancelled"])),
                name="chk_dro_sop_dlv_sts",
            ),
        ),
        migrations.AddIndex(
            model_name="dronesoptargetdispatch",
            index=models.Index(fields=["sop", "status"], name="idx_dro_sop_tgt_dsp_sop"),
        ),
        migrations.AddIndex(
            model_name="dronesoptargetdispatch",
            index=models.Index(fields=["target_code_snapshot"], name="idx_dro_sop_tgt_dsp_cd"),
        ),
        migrations.AddIndex(
            model_name="dronesopdelivery",
            index=models.Index(fields=["dispatch", "channel"], name="idx_dro_sop_dlv_dsp"),
        ),
        migrations.CreateModel(
            name="DroneSopDeliveryAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("attempt_no", models.PositiveIntegerField()),
                (
                    "status",
                    models.CharField(
                        choices=[("sending", "Sending"), ("success", "Success"), ("failed", "Failed")],
                        default="sending",
                        max_length=16,
                    ),
                ),
                ("sent_comment_snapshot", models.TextField(blank=True, null=True)),
                ("sent_step_snapshot", models.CharField(blank=True, max_length=50, null=True)),
                ("request_snapshot", models.JSONField(blank=True, null=True)),
                ("response_snapshot", models.JSONField(blank=True, null=True)),
                ("error_code", models.CharField(blank=True, max_length=64, null=True)),
                ("error_message", models.TextField(blank=True, null=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_default=django.db.models.functions.Now())),
                ("updated_at", models.DateTimeField(auto_now=True, db_default=django.db.models.functions.Now())),
                (
                    "delivery",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attempts",
                        to="drone.dronesopdelivery",
                    ),
                ),
            ],
            options={
                "db_table": "drone_sop_delivery_attempt",
            },
        ),
        migrations.AddConstraint(
            model_name="dronesopdeliveryattempt",
            constraint=models.UniqueConstraint(
                fields=("delivery", "attempt_no"),
                name="uniq_dro_sop_dlv_att_no",
            ),
        ),
        migrations.AddConstraint(
            model_name="dronesopdeliveryattempt",
            constraint=models.CheckConstraint(
                condition=models.Q(("status__in", ["sending", "success", "failed"])),
                name="chk_dro_sop_dlv_att_st",
            ),
        ),
        migrations.AddIndex(
            model_name="dronesopdeliveryattempt",
            index=models.Index(fields=["delivery", "attempt_no"], name="idx_dro_sop_dlv_att_dlv"),
        ),
        migrations.AddIndex(
            model_name="dronesopdeliveryattempt",
            index=models.Index(fields=["status", "started_at"], name="idx_dro_sop_dlv_att_st"),
        ),
    ]
