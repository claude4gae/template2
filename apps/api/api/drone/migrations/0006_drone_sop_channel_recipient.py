import django.db.models.deletion
import django.db.models.functions.datetime
from django.conf import settings
from django.db import migrations, models


def _backfill_channel_recipients(apps, schema_editor):  # pragma: no cover
    """현재 account_user.user_sdwt_prod 기준으로 초기 수신인 스냅샷을 생성합니다."""

    User = apps.get_model("account", "User")
    DroneSopChannelRecipient = apps.get_model("drone", "DroneSopChannelRecipient")
    batch_size = 1000

    rows = []

    def flush_rows():
        """누적된 수신인 row를 배치 단위로 저장합니다."""

        if not rows:
            return
        DroneSopChannelRecipient.objects.bulk_create(rows, ignore_conflicts=True, batch_size=batch_size)
        rows.clear()

    base_users = (
        User.objects.filter(is_active=True)
        .exclude(user_sdwt_prod__isnull=True)
        .exclude(user_sdwt_prod__exact="")
        .only("id", "user_sdwt_prod", "email", "knox_id")
        .order_by("id")
    )

    for user in base_users.iterator():
        target = (user.user_sdwt_prod or "").strip()
        if not target:
            continue
        if isinstance(user.email, str) and user.email.strip():
            rows.append(
                DroneSopChannelRecipient(
                    target_user_sdwt_prod=target,
                    channel="mail",
                    user_id=user.id,
                    is_active=True,
                    created_by_id=None,
                )
            )
        if isinstance(user.knox_id, str) and user.knox_id.strip():
            rows.append(
                DroneSopChannelRecipient(
                    target_user_sdwt_prod=target,
                    channel="messenger",
                    user_id=user.id,
                    is_active=True,
                    created_by_id=None,
                )
            )
        if len(rows) >= batch_size:
            flush_rows()

    flush_rows()


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("drone", "0005_backfill_messenger_template_key"),
    ]

    operations = [
        migrations.CreateModel(
            name="DroneSopChannelRecipient",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("target_user_sdwt_prod", models.CharField(max_length=64)),
                ("channel", models.CharField(choices=[("mail", "Mail"), ("messenger", "Messenger")], max_length=16)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, db_default=django.db.models.functions.datetime.Now()),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, db_default=django.db.models.functions.datetime.Now()),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_drone_sop_recipients",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="drone_sop_recipients",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "drone_sop_channel_recipient",
                "indexes": [
                    models.Index(fields=["target_user_sdwt_prod", "channel"], name="idx_dro_sop_chn_rcp_tgt"),
                    models.Index(fields=["user"], name="idx_dro_sop_chn_rcp_usr"),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("target_user_sdwt_prod", "channel", "user"),
                        name="uniq_dro_sop_chn_rcp_usr",
                    ),
                ],
            },
        ),
        migrations.RunPython(_backfill_channel_recipients, migrations.RunPython.noop),
    ]
