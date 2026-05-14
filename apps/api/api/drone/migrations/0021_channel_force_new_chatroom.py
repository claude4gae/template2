from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("drone", "0020_normalize_target_channel_config"),
    ]

    operations = [
        migrations.AddField(
            model_name="dronesoptargetchannelconfig",
            name="force_new_chatroom",
            field=models.BooleanField(default=False),
        ),
    ]
