from django.db import migrations, models
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils import timezone


def deactivate_duplicate_active_mappings(apps, schema_editor):
    DroneSopTargetMapping = apps.get_model("drone", "DroneSopTargetMapping")
    seen = set()
    duplicate_ids = []

    rows = (
        DroneSopTargetMapping.objects.filter(is_active=True)
        .order_by("id")
        .values("id", "sdwt_prod", "user_sdwt_prod")
    )
    for row in rows:
        sdwt_prod = str(row.get("sdwt_prod") or "").strip().casefold()
        user_sdwt_prod = str(row.get("user_sdwt_prod") or "").strip().casefold()
        if sdwt_prod and user_sdwt_prod:
            key = ("pair", sdwt_prod, user_sdwt_prod)
        elif sdwt_prod:
            key = ("sdwt", sdwt_prod)
        elif user_sdwt_prod:
            key = ("user", user_sdwt_prod)
        else:
            continue

        if key in seen:
            duplicate_ids.append(row["id"])
            continue
        seen.add(key)

    if duplicate_ids:
        DroneSopTargetMapping.objects.filter(id__in=duplicate_ids).update(
            is_active=False,
            updated_at=timezone.now(),
        )


class Migration(migrations.Migration):
    dependencies = [
        ("drone", "0013_target_fk_delivery_architecture"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="dronesoptargetmapping",
            name="uniq_dro_sop_tgt_map_pair",
        ),
        migrations.RemoveConstraint(
            model_name="dronesoptargetmapping",
            name="uniq_dro_sop_tgt_map_sdw",
        ),
        migrations.RemoveConstraint(
            model_name="dronesoptargetmapping",
            name="uniq_dro_sop_tgt_map_usr",
        ),
        migrations.RunPython(deactivate_duplicate_active_mappings, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="dronesoptargetmapping",
            constraint=models.UniqueConstraint(
                Lower("sdwt_prod"),
                Lower("user_sdwt_prod"),
                condition=(
                    Q(("sdwt_prod__isnull", False))
                    & ~Q(("sdwt_prod", ""))
                    & Q(("user_sdwt_prod__isnull", False))
                    & ~Q(("user_sdwt_prod", ""))
                    & Q(("is_active", True))
                ),
                name="uniq_dro_tgt_map_pair_act",
            ),
        ),
        migrations.AddConstraint(
            model_name="dronesoptargetmapping",
            constraint=models.UniqueConstraint(
                Lower("sdwt_prod"),
                condition=(
                    Q(("sdwt_prod__isnull", False))
                    & ~Q(("sdwt_prod", ""))
                    & (Q(("user_sdwt_prod__isnull", True)) | Q(("user_sdwt_prod", "")))
                    & Q(("is_active", True))
                ),
                name="uniq_dro_tgt_map_sdw_act",
            ),
        ),
        migrations.AddConstraint(
            model_name="dronesoptargetmapping",
            constraint=models.UniqueConstraint(
                Lower("user_sdwt_prod"),
                condition=(
                    Q(("user_sdwt_prod__isnull", False))
                    & ~Q(("user_sdwt_prod", ""))
                    & (Q(("sdwt_prod__isnull", True)) | Q(("sdwt_prod", "")))
                    & Q(("is_active", True))
                ),
                name="uniq_dro_tgt_map_usr_act",
            ),
        ),
    ]
