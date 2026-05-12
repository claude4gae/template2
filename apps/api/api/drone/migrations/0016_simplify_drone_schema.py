from django.db import migrations, models
import django.db.models.functions.text
from django.db.models import Q


def backfill_sop_target_from_delivery(apps, schema_editor):
    """기존 delivery target FK에서 SOP target snapshot을 채웁니다."""

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE drone_sop AS sop
            SET target_user_sdwt_prod = ranked.target_user_sdwt_prod
            FROM (
                SELECT DISTINCT ON (delivery.sop_id)
                    delivery.sop_id,
                    target.target_user_sdwt_prod
                FROM drone_sop_delivery AS delivery
                INNER JOIN drone_sop_target AS target
                    ON target.id = delivery.target_id
                WHERE target.target_user_sdwt_prod IS NOT NULL
                  AND target.target_user_sdwt_prod <> ''
                ORDER BY
                    delivery.sop_id,
                    CASE
                        WHEN target.target_user_sdwt_prod LIKE '__%%' THEN 1
                        ELSE 0
                    END,
                    delivery.id
            ) AS ranked
            WHERE sop.id = ranked.sop_id
              AND (sop.target_user_sdwt_prod IS NULL OR sop.target_user_sdwt_prod = '')
            """
        )


def squash_duplicate_deliveries(apps, schema_editor):
    """target 제거 전 SOP/channel 기준 delivery를 하나로 정리합니다."""

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM drone_sop_delivery AS delivery
            USING (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY sop_id, channel
                        ORDER BY
                            CASE status
                                WHEN 'success' THEN 0
                                WHEN 'pending' THEN 1
                                WHEN 'failed' THEN 2
                                WHEN 'disabled' THEN 3
                                ELSE 4
                            END,
                            id
                    ) AS row_num
                FROM drone_sop_delivery
            ) AS ranked
            WHERE delivery.id = ranked.id
              AND ranked.row_num > 1
            """
        )


def delete_inactive_target_rows(apps, schema_editor):
    """기존 비활성 설정 row를 hard-delete 기준으로 정리합니다."""

    DroneSopTarget = apps.get_model("drone", "DroneSopTarget")
    DroneSopTargetMapping = apps.get_model("drone", "DroneSopTargetMapping")
    db_alias = schema_editor.connection.alias

    DroneSopTargetMapping.objects.using(db_alias).filter(is_active=False).delete()
    DroneSopTarget.objects.using(db_alias).filter(is_active=False).delete()


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("drone", "0015_remove_recipient_is_active"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="dronesop",
            name="uniq_dro_sop_ln_id_eqp_i_92d25",
        ),
        migrations.RemoveIndex(
            model_name="dronesop",
            name="idx_dro_sop_knx_id",
        ),
        migrations.AddField(
            model_name="dronesop",
            name="target_user_sdwt_prod",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddIndex(
            model_name="dronesop",
            index=models.Index(
                fields=["target_user_sdwt_prod", "created_at", "id"],
                name="idx_dro_sop_tgt_crt_id",
            ),
        ),
        migrations.RunPython(backfill_sop_target_from_delivery, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name="dronesopdelivery",
            name="uniq_dro_sop_delivery",
        ),
        migrations.RemoveIndex(
            model_name="dronesopdelivery",
            name="idx_dro_sop_dlv_tgt",
        ),
        migrations.RunPython(squash_duplicate_deliveries, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="dronesopdelivery",
            name="target",
        ),
        migrations.AddConstraint(
            model_name="dronesopdelivery",
            constraint=models.UniqueConstraint(
                fields=("sop", "channel"),
                name="uniq_dro_sop_delivery",
            ),
        ),
        migrations.RunPython(delete_inactive_target_rows, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name="dronesoptargetmapping",
            name="uniq_dro_tgt_map_pair_act",
        ),
        migrations.RemoveConstraint(
            model_name="dronesoptargetmapping",
            name="uniq_dro_tgt_map_sdw_act",
        ),
        migrations.RemoveConstraint(
            model_name="dronesoptargetmapping",
            name="uniq_dro_tgt_map_usr_act",
        ),
        migrations.RemoveField(
            model_name="dronesoptarget",
            name="source",
        ),
        migrations.RemoveField(
            model_name="dronesoptarget",
            name="created_by",
        ),
        migrations.RemoveField(
            model_name="dronesoptarget",
            name="is_active",
        ),
        migrations.RemoveField(
            model_name="dronesoptargetmapping",
            name="is_active",
        ),
        migrations.RemoveField(
            model_name="dronesoptargetrecipient",
            name="created_by",
        ),
        migrations.AddConstraint(
            model_name="dronesoptargetmapping",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("sdwt_prod"),
                django.db.models.functions.text.Lower("user_sdwt_prod"),
                condition=(
                    Q(("sdwt_prod__isnull", False))
                    & ~Q(("sdwt_prod", ""))
                    & Q(("user_sdwt_prod__isnull", False))
                    & ~Q(("user_sdwt_prod", ""))
                ),
                name="uniq_dro_tgt_map_pair",
            ),
        ),
        migrations.AddConstraint(
            model_name="dronesoptargetmapping",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("sdwt_prod"),
                condition=(
                    Q(("sdwt_prod__isnull", False))
                    & ~Q(("sdwt_prod", ""))
                    & (Q(("user_sdwt_prod__isnull", True)) | Q(("user_sdwt_prod", "")))
                ),
                name="uniq_dro_tgt_map_sdw",
            ),
        ),
        migrations.AddConstraint(
            model_name="dronesoptargetmapping",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("user_sdwt_prod"),
                condition=(
                    Q(("user_sdwt_prod__isnull", False))
                    & ~Q(("user_sdwt_prod", ""))
                    & (Q(("sdwt_prod__isnull", True)) | Q(("sdwt_prod", "")))
                ),
                name="uniq_dro_tgt_map_usr",
            ),
        ),
    ]
