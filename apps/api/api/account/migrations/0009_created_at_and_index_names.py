from __future__ import annotations

from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0008_user_userid"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="affiliation",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name="affiliation",
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name="usersdwtprodaccess",
            unique_together=set(),
        ),
        migrations.RemoveConstraint(
            model_name="affiliation",
            name="uniq_aff_line_user_sdwt",
        ),
        migrations.AddConstraint(
            model_name="affiliation",
            constraint=models.UniqueConstraint(
                fields=("department", "line", "user_sdwt_prod"),
                name="uniq_acc_aff_dep_ln_usr_724c6",
            ),
        ),
        migrations.AddConstraint(
            model_name="affiliation",
            constraint=models.UniqueConstraint(
                fields=("line", "user_sdwt_prod"),
                name="uniq_acc_aff_ln_usr_sdw_prd",
            ),
        ),
        migrations.AddConstraint(
            model_name="usersdwtprodaccess",
            constraint=models.UniqueConstraint(
                fields=("user", "user_sdwt_prod"),
                name="uniq_acc_usr_sdw_prd_acs_02885",
            ),
        ),
        migrations.RenameIndex(
            model_name="affiliation",
            old_name="aff_hier_department",
            new_name="idx_acc_aff_dep",
        ),
        migrations.RenameIndex(
            model_name="affiliation",
            old_name="aff_hier_line",
            new_name="idx_acc_aff_ln",
        ),
        migrations.RenameIndex(
            model_name="affiliation",
            old_name="aff_hier_user_sdwt_prod",
            new_name="idx_acc_aff_usr_sdw_prd",
        ),
        migrations.RenameIndex(
            model_name="affiliation",
            old_name="aff_line_user_sdwt",
            new_name="idx_acc_aff_ln_usr_sdw_prd",
        ),
        migrations.RenameIndex(
            model_name="usersdwtprodaccess",
            old_name="user_sdwt_access_user",
            new_name="idx_acc_usr_sdw_prd_acs_usr",
        ),
        migrations.RenameIndex(
            model_name="usersdwtprodaccess",
            old_name="user_sdwt_access_prod",
            new_name="idx_acc_usr_sdw_prd_acs_1a1f0",
        ),
        migrations.RenameIndex(
            model_name="usersdwtprodchange",
            old_name="user_sdwt_change_eff",
            new_name="idx_acc_usr_sdw_prd_chg_364a4",
        ),
        migrations.RenameIndex(
            model_name="usersdwtprodchange",
            old_name="user_sdwt_change_applied",
            new_name="idx_acc_usr_sdw_prd_chg_app",
        ),
        migrations.RenameIndex(
            model_name="externalaffiliationsnapshot",
            old_name="idx_ext_aff_snap_sdwt",
            new_name="idx_acc_ext_aff_snp_pred_54654",
        ),
        migrations.RenameIndex(
            model_name="externalaffiliationsnapshot",
            old_name="idx_ext_aff_snap_src_upd",
            new_name="idx_acc_ext_aff_snp_src_upd_at",
        ),
    ]
