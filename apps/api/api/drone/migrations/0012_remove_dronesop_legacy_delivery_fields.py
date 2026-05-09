from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("drone", "0011_backfill_delivery_snapshots"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="dronesop",
            name="idx_dro_sop_snd_jir_nts",
        ),
        migrations.RemoveIndex(
            model_name="dronesop",
            name="idx_dro_sop_snd_jir",
        ),
        migrations.RemoveIndex(
            model_name="dronesop",
            name="idx_dro_sop_id_jir_pen",
        ),
        migrations.RemoveField(
            model_name="dronesop",
            name="jira_reason",
        ),
        migrations.RemoveField(
            model_name="dronesop",
            name="mail_reason",
        ),
        migrations.RemoveField(
            model_name="dronesop",
            name="messenger_reason",
        ),
        migrations.RemoveField(
            model_name="dronesop",
            name="send_jira",
        ),
        migrations.RemoveField(
            model_name="dronesop",
            name="send_mail",
        ),
        migrations.RemoveField(
            model_name="dronesop",
            name="send_messenger",
        ),
        migrations.RemoveField(
            model_name="dronesop",
            name="target_user_sdwt_prod",
        ),
    ]
