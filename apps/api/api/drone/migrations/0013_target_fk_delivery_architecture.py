import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


SYSTEM_TARGET_LEGACY = "__legacy_target__"


def _normalize_target_name(value):
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _get_or_create_target(DroneSopTarget, target_name):
    normalized = _normalize_target_name(target_name) or SYSTEM_TARGET_LEGACY
    target, _ = DroneSopTarget.objects.get_or_create(
        target_user_sdwt_prod=normalized,
        defaults={
            "line_id": "",
            "source": "system" if normalized.startswith("__") else "custom",
            "is_active": False,
        },
    )
    return target


def backfill_target_fks(apps, schema_editor):
    DroneSopTarget = apps.get_model("drone", "DroneSopTarget")
    DroneSopTargetMapping = apps.get_model("drone", "DroneSopTargetMapping")
    DroneSopTargetRecipient = apps.get_model("drone", "DroneSopTargetRecipient")
    DroneSopDelivery = apps.get_model("drone", "DroneSopDelivery")

    for mapping in DroneSopTargetMapping.objects.filter(target__isnull=True).iterator(chunk_size=1000):
        mapping.target = _get_or_create_target(DroneSopTarget, getattr(mapping, "target_user_sdwt_prod", None))
        mapping.save(update_fields=["target"])

    for recipient in DroneSopTargetRecipient.objects.filter(target__isnull=True).iterator(chunk_size=1000):
        recipient.target = _get_or_create_target(DroneSopTarget, getattr(recipient, "target_user_sdwt_prod", None))
        recipient.save(update_fields=["target"])

    for delivery in DroneSopDelivery.objects.filter(target__isnull=True).iterator(chunk_size=1000):
        delivery.target = _get_or_create_target(DroneSopTarget, getattr(delivery, "target_user_sdwt_prod", None))
        delivery.save(update_fields=["target"])


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("drone", "0012_remove_dronesop_legacy_delivery_fields"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="DroneSopUserSdwtChannel",
            new_name="DroneSopTarget",
        ),
        migrations.RenameModel(
            old_name="DroneSopUserSdwtProdMap",
            new_name="DroneSopTargetMapping",
        ),
        migrations.RenameModel(
            old_name="DroneSopChannelRecipient",
            new_name="DroneSopTargetRecipient",
        ),
        migrations.RenameModel(
            old_name="DroneSopChannelDelivery",
            new_name="DroneSopDelivery",
        ),
        migrations.AlterModelTable(
            name="dronesoptarget",
            table="drone_sop_target",
        ),
        migrations.AlterModelTable(
            name="dronesoptargetmapping",
            table="drone_sop_target_mapping",
        ),
        migrations.AlterModelTable(
            name="dronesoptargetrecipient",
            table="drone_sop_target_recipient",
        ),
        migrations.AlterModelTable(
            name="dronesopdelivery",
            table="drone_sop_delivery",
        ),
        migrations.RemoveConstraint(
            model_name="dronesoptarget",
            name="uniq_dro_sop_usr_chn",
        ),
        migrations.RemoveIndex(
            model_name="dronesoptarget",
            name="idx_dro_sop_usr_chn_ln",
        ),
        migrations.RemoveConstraint(
            model_name="dronesoptargetmapping",
            name="chk_dro_sop_sdw_usr_req",
        ),
        migrations.RemoveConstraint(
            model_name="dronesoptargetmapping",
            name="uniq_dro_sop_sdw_usr_tgt",
        ),
        migrations.RemoveConstraint(
            model_name="dronesoptargetmapping",
            name="uniq_dro_sop_sdw_tgt",
        ),
        migrations.RemoveConstraint(
            model_name="dronesoptargetmapping",
            name="uniq_dro_sop_usr_tgt",
        ),
        migrations.RemoveConstraint(
            model_name="dronesoptargetrecipient",
            name="uniq_dro_sop_chn_rcp_usr",
        ),
        migrations.RemoveIndex(
            model_name="dronesoptargetrecipient",
            name="idx_dro_sop_chn_rcp_tgt",
        ),
        migrations.RemoveIndex(
            model_name="dronesoptargetrecipient",
            name="idx_dro_sop_chn_rcp_usr",
        ),
        migrations.RemoveConstraint(
            model_name="dronesopdelivery",
            name="uniq_dro_sop_chn_dlv",
        ),
        migrations.RemoveIndex(
            model_name="dronesopdelivery",
            name="idx_dro_sop_chn_dlv_sop",
        ),
        migrations.RemoveIndex(
            model_name="dronesopdelivery",
            name="idx_dro_sop_chn_dlv_tgt",
        ),
        migrations.RemoveIndex(
            model_name="dronesopdelivery",
            name="idx_dro_sop_chn_dlv_sts",
        ),
        migrations.AddField(
            model_name="dronesoptargetmapping",
            name="target",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="mappings",
                to="drone.dronesoptarget",
            ),
        ),
        migrations.AddField(
            model_name="dronesoptargetrecipient",
            name="target",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="recipients",
                to="drone.dronesoptarget",
            ),
        ),
        migrations.AddField(
            model_name="dronesopdelivery",
            name="target",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="deliveries",
                to="drone.dronesoptarget",
            ),
        ),
        migrations.AddField(
            model_name="dronesopdelivery",
            name="sent_step",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.RunPython(backfill_target_fks, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="dronesoptargetmapping",
            name="target_user_sdwt_prod",
        ),
        migrations.RemoveField(
            model_name="dronesoptargetrecipient",
            name="target_user_sdwt_prod",
        ),
        migrations.RemoveField(
            model_name="dronesopdelivery",
            name="target_user_sdwt_prod",
        ),
        migrations.RemoveField(
            model_name="dronesop",
            name="inform_step",
        ),
        migrations.RemoveField(
            model_name="dronesop",
            name="jira_key",
        ),
        migrations.RemoveField(
            model_name="dronesop",
            name="informed_at",
        ),
        migrations.AlterField(
            model_name="dronesoptargetmapping",
            name="target",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="mappings",
                to="drone.dronesoptarget",
            ),
        ),
        migrations.AlterField(
            model_name="dronesoptargetrecipient",
            name="target",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="recipients",
                to="drone.dronesoptarget",
            ),
        ),
        migrations.AlterField(
            model_name="dronesopdelivery",
            name="target",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="deliveries",
                to="drone.dronesoptarget",
            ),
        ),
        migrations.AddConstraint(
            model_name="dronesoptarget",
            constraint=models.UniqueConstraint(fields=("target_user_sdwt_prod",), name="uniq_dro_sop_target"),
        ),
        migrations.AddIndex(
            model_name="dronesoptarget",
            index=models.Index(fields=["line_id"], name="idx_dro_sop_tgt_line"),
        ),
        migrations.AlterField(
            model_name="dronesoptarget",
            name="source",
            field=models.CharField(
                choices=[("affiliation", "Affiliation"), ("custom", "Custom"), ("system", "System")],
                default="custom",
                max_length=20,
            ),
        ),
        migrations.AddConstraint(
            model_name="dronesoptargetmapping",
            constraint=models.CheckConstraint(
                check=(
                    (Q(("sdwt_prod__isnull", False)) & ~Q(("sdwt_prod", "")))
                    | (Q(("user_sdwt_prod__isnull", False)) & ~Q(("user_sdwt_prod", "")))
                ),
                name="chk_dro_sop_tgt_map_req",
            ),
        ),
        migrations.AddConstraint(
            model_name="dronesoptargetmapping",
            constraint=models.UniqueConstraint(
                fields=("sdwt_prod", "user_sdwt_prod", "target"),
                condition=(
                    Q(("sdwt_prod__isnull", False))
                    & ~Q(("sdwt_prod", ""))
                    & Q(("user_sdwt_prod__isnull", False))
                    & ~Q(("user_sdwt_prod", ""))
                ),
                name="uniq_dro_sop_tgt_map_pair",
            ),
        ),
        migrations.AddConstraint(
            model_name="dronesoptargetmapping",
            constraint=models.UniqueConstraint(
                fields=("sdwt_prod", "target"),
                condition=(
                    Q(("sdwt_prod__isnull", False))
                    & ~Q(("sdwt_prod", ""))
                    & (Q(("user_sdwt_prod__isnull", True)) | Q(("user_sdwt_prod", "")))
                ),
                name="uniq_dro_sop_tgt_map_sdw",
            ),
        ),
        migrations.AddConstraint(
            model_name="dronesoptargetmapping",
            constraint=models.UniqueConstraint(
                fields=("user_sdwt_prod", "target"),
                condition=(
                    Q(("user_sdwt_prod__isnull", False))
                    & ~Q(("user_sdwt_prod", ""))
                    & (Q(("sdwt_prod__isnull", True)) | Q(("sdwt_prod", "")))
                ),
                name="uniq_dro_sop_tgt_map_usr",
            ),
        ),
        migrations.AddConstraint(
            model_name="dronesoptargetrecipient",
            constraint=models.UniqueConstraint(fields=("target", "channel", "user"), name="uniq_dro_sop_tgt_rcp_usr"),
        ),
        migrations.AddIndex(
            model_name="dronesoptargetrecipient",
            index=models.Index(fields=["target", "channel"], name="idx_dro_sop_tgt_rcp_tgt"),
        ),
        migrations.AddIndex(
            model_name="dronesoptargetrecipient",
            index=models.Index(fields=["user"], name="idx_dro_sop_tgt_rcp_usr"),
        ),
        migrations.AddConstraint(
            model_name="dronesopdelivery",
            constraint=models.UniqueConstraint(fields=("sop", "target", "channel"), name="uniq_dro_sop_delivery"),
        ),
        migrations.AddIndex(
            model_name="dronesopdelivery",
            index=models.Index(fields=["sop", "channel"], name="idx_dro_sop_dlv_sop"),
        ),
        migrations.AddIndex(
            model_name="dronesopdelivery",
            index=models.Index(fields=["target", "channel", "status"], name="idx_dro_sop_dlv_tgt"),
        ),
        migrations.AddIndex(
            model_name="dronesopdelivery",
            index=models.Index(fields=["channel", "status"], name="idx_dro_sop_dlv_sts"),
        ),
    ]
