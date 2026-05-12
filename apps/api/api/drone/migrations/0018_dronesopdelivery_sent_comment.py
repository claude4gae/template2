from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("drone", "0017_normalize_delivery_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="dronesopdelivery",
            name="sent_comment",
            field=models.TextField(blank=True, null=True),
        ),
    ]
