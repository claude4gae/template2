from __future__ import annotations

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("drone", "0007_created_at_and_index_names"),
    ]

    operations = [
        migrations.DeleteModel(
            name="DroneSopJiraTemplate",
        ),
    ]
