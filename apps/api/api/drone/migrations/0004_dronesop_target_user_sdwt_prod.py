from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("drone", "0003_dronesop_defect_png_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="dronesop",
            name="target_user_sdwt_prod",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
    ]
