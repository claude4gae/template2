from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("voc", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="vocpost",
            name="app",
            field=models.CharField(
                choices=[("기타", "기타")],
                default="기타",
                max_length=80,
            ),
        ),
    ]
