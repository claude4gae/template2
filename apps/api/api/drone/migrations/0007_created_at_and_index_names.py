from __future__ import annotations

from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):
    dependencies = [
        ("drone", "0006_drone_sop_jira_pending_index"),
    ]

    operations = [
        migrations.AddField(
            model_name="droneearlyinform",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.RemoveConstraint(
            model_name="dronesop",
            name="uniq_row",
        ),
        migrations.AddConstraint(
            model_name="dronesop",
            constraint=models.UniqueConstraint(
                fields=("line_id", "eqp_id", "chamber_ids", "lot_id", "main_step"),
                name="uniq_dro_sop_ln_id_eqp_i_92d25",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="droneearlyinform",
            name="uniq_line_mainstep",
        ),
        migrations.AddConstraint(
            model_name="droneearlyinform",
            constraint=models.UniqueConstraint(
                fields=("line_id", "main_step"),
                name="uniq_dro_erl_inf_ln_id_mn_stp",
            ),
        ),
        migrations.RenameIndex(
            model_name="dronesop",
            old_name="send_jira_needtosend",
            new_name="idx_dro_sop_snd_jir_nts",
        ),
        migrations.RenameIndex(
            model_name="dronesop",
            old_name="sdwt_prod",
            new_name="idx_dro_sop_sdw_prd",
        ),
        migrations.RenameIndex(
            model_name="dronesop",
            old_name="drone_sop_created_at_id",
            new_name="idx_dro_sop_crt_at_id",
        ),
        migrations.RenameIndex(
            model_name="dronesop",
            old_name="dsop_usr_sdwt_created_id",
            new_name="idx_dro_sop_usr_sdw_prd_dd5e5",
        ),
        migrations.RenameIndex(
            model_name="dronesop",
            old_name="drone_sop_send_jira",
            new_name="idx_dro_sop_snd_jir",
        ),
        migrations.RenameIndex(
            model_name="dronesop",
            old_name="drone_sop_knoxid",
            new_name="idx_dro_sop_knx_id",
        ),
        migrations.RenameIndex(
            model_name="dronesop",
            old_name="drone_sop_jira_pending",
            new_name="idx_dro_sop_id_jir_pen",
        ),
        migrations.RenameIndex(
            model_name="dronesopjiratemplate",
            old_name="drone_jira_tpl_line",
            new_name="idx_dro_sop_jir_tmpl_ln_id",
        ),
        migrations.RenameIndex(
            model_name="dronesopjirausertemplate",
            old_name="drone_jira_tpl_user",
            new_name="idx_dro_sop_jir_usr_tmpl_a256d",
        ),
    ]
