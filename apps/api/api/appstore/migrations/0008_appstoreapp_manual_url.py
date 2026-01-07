from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("appstore", "0007_index_and_constraint_names"),
    ]

    operations = [
        migrations.AddField(
            model_name="appstoreapp",
            name="manual_url",
            field=models.TextField(blank=True, null=True),
        ),
    ]
