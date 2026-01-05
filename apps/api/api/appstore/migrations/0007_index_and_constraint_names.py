from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("appstore", "0006_remove_appstoreapp_tags_badge"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="appstorelike",
            unique_together=set(),
        ),
        migrations.RemoveConstraint(
            model_name="appstorecommentlike",
            name="uniq_appstore_cmtlike_cmt_user",
        ),
        migrations.AddConstraint(
            model_name="appstorelike",
            constraint=models.UniqueConstraint(
                fields=("app", "user"),
                name="uniq_aps_lik_app_usr",
            ),
        ),
        migrations.AddConstraint(
            model_name="appstorecommentlike",
            constraint=models.UniqueConstraint(
                fields=("comment", "user"),
                name="uniq_aps_cmt_lik_cmt_usr",
            ),
        ),
        migrations.RenameIndex(
            model_name="appstoreapp",
            old_name="appstore_app_category_idx",
            new_name="idx_aps_app_cat",
        ),
        migrations.RenameIndex(
            model_name="appstoreapp",
            old_name="appstore_app_name_idx",
            new_name="idx_aps_app_nam",
        ),
        migrations.RenameIndex(
            model_name="appstorecomment",
            old_name="appstore_comment_app_idx",
            new_name="idx_aps_cmt_app",
        ),
        migrations.RenameIndex(
            model_name="appstorecomment",
            old_name="appstore_comment_created_idx",
            new_name="idx_aps_cmt_app_crt_at",
        ),
        migrations.RenameIndex(
            model_name="appstorecomment",
            old_name="appstore_comment_parent_idx",
            new_name="idx_aps_cmt_par",
        ),
        migrations.RenameIndex(
            model_name="appstorelike",
            old_name="appstore_like_user_idx",
            new_name="idx_aps_lik_usr",
        ),
        migrations.RenameIndex(
            model_name="appstorelike",
            old_name="appstore_like_app_idx",
            new_name="idx_aps_lik_app",
        ),
        migrations.RenameIndex(
            model_name="appstorecommentlike",
            old_name="idx_appstore_cmtlike_user",
            new_name="idx_aps_cmt_lik_usr",
        ),
        migrations.RenameIndex(
            model_name="appstorecommentlike",
            old_name="idx_appstore_cmtlike_comment",
            new_name="idx_aps_cmt_lik_cmt",
        ),
    ]
