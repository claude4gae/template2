from __future__ import annotations

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0010_affiliation_user_sdwt_unique"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="affiliation",
            name="jira_key",
        ),
    ]
