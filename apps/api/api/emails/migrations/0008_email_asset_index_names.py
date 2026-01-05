from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("emails", "0007_rename_email_asset_indexes"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="email",
            old_name="idx_emails_inbox_recipient_gin",
            new_name="idx_eml_inb_rcp_gin",
        ),
        migrations.RenameIndex(
            model_name="email",
            old_name="idx_emails_inbox_cc_gin",
            new_name="idx_eml_inb_cc_gin",
        ),
        migrations.RenameIndex(
            model_name="email",
            old_name="idx_emails_inbox_part_trgm",
            new_name="idx_eml_inb_par_trg",
        ),
        migrations.RenameIndex(
            model_name="emailoutbox",
            old_name="idx_emails_outbox_status_time",
            new_name="idx_eml_out_sts_tm",
        ),
        migrations.RenameIndex(
            model_name="emailasset",
            old_name="idx_emails_email_asset_email",
            new_name="idx_eml_eml_ast_eml",
        ),
        migrations.RenameIndex(
            model_name="emailasset",
            old_name="idx_emails_asset_ocr_status",
            new_name="idx_eml_eml_ast_ocr_sts",
        ),
        migrations.RenameIndex(
            model_name="emailasset",
            old_name="idx_emails_asset_ocr_lock",
            new_name="idx_eml_eml_ast_ocr_lk_exp_at",
        ),
        migrations.RemoveConstraint(
            model_name="emailasset",
            name="uniq_emails_email_asset_email_sequence",
        ),
        migrations.AddConstraint(
            model_name="emailasset",
            constraint=models.UniqueConstraint(
                fields=("email", "sequence"),
                name="uniq_eml_eml_ast_eml_seq",
            ),
        ),
    ]
