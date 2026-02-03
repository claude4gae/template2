from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0013_user_sdwt_prod_access_role"),
    ]

    operations = [
        migrations.AddField(
            model_name="externalaffiliationsnapshot",
            name="department",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="externalaffiliationsnapshot",
            name="line",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
    ]
