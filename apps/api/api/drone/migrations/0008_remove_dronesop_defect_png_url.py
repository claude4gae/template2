from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("drone", "0007_add_notification_target_scope"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="dronesop",
            name="defect_png_url",
        ),
    ]
