from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("drone", "0022_external_target_recipients"),
    ]

    operations = [
        migrations.DeleteModel(
            name="DroneSopDeliveryAttempt",
        ),
    ]
