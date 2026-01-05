from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("drone", "0008_remove_drone_sop_jira_template"),
    ]

    operations = [
        migrations.AddField(
            model_name="dronesopjirausertemplate",
            name="jira_key",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AlterField(
            model_name="dronesopjirausertemplate",
            name="template_key",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
