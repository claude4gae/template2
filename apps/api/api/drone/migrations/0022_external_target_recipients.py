import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("drone", "0021_channel_force_new_chatroom"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="dronesoptargetrecipient",
            name="uniq_dro_sop_tgt_rcp_usr",
        ),
        migrations.AlterField(
            model_name="dronesoptargetrecipient",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="drone_sop_recipients",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="dronesoptargetrecipient",
            name="external_knox_id",
            field=models.CharField(blank=True, default="", max_length=150),
        ),
        migrations.AddConstraint(
            model_name="dronesoptargetrecipient",
            constraint=models.UniqueConstraint(
                condition=Q(("user__isnull", False)),
                fields=("target", "channel", "user"),
                name="uniq_dro_sop_tgt_rcp_usr",
            ),
        ),
        migrations.AddConstraint(
            model_name="dronesoptargetrecipient",
            constraint=models.UniqueConstraint(
                condition=~Q(("external_knox_id", "")),
                fields=("target", "channel", "external_knox_id"),
                name="uniq_dro_sop_tgt_rcp_ext",
            ),
        ),
        migrations.AddConstraint(
            model_name="dronesoptargetrecipient",
            constraint=models.CheckConstraint(
                check=Q(("external_knox_id", ""), ("user__isnull", False))
                | (Q(("user__isnull", True)) & ~Q(("external_knox_id", ""))),
                name="chk_dro_sop_tgt_rcp_one",
            ),
        ),
        migrations.AddIndex(
            model_name="dronesoptargetrecipient",
            index=models.Index(fields=["external_knox_id"], name="idx_dro_sop_tgt_rcp_ext"),
        ),
    ]
