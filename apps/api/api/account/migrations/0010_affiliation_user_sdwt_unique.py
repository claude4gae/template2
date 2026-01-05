from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0009_created_at_and_index_names"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="affiliation",
            name="uniq_acc_aff_dep_ln_usr_724c6",
        ),
        migrations.RemoveConstraint(
            model_name="affiliation",
            name="uniq_acc_aff_ln_usr_sdw_prd",
        ),
        migrations.AddConstraint(
            model_name="affiliation",
            constraint=models.UniqueConstraint(
                fields=("user_sdwt_prod",),
                name="uniq_acc_aff_usr_sdw_prd",
            ),
        ),
    ]
