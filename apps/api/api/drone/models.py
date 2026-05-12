# =============================================================================
# 모듈: 드론 SOP/조기 알림 모델
# 주요 구성: DroneSOP, DroneSopTarget, DroneSopTargetDispatch, DroneSopDelivery, DroneEarlyInform
# 주요 가정: sop_key는 필드 조합으로 생성합니다.
# =============================================================================
from __future__ import annotations

from django.conf import settings
from django.db import IntegrityError, models
from django.db.models import Q
from django.db.models.functions import Lower, Now


def build_sop_key(
    *,
    line_id: str | None,
    eqp_id: str | None,
    chamber_ids: str | None,
    lot_id: str | None,
    main_step: str | None,
) -> str:
    """Drone SOP 식별용 sop_key를 생성합니다.

    인자:
        line_id: 라인 ID.
        eqp_id: 장비 ID.
        chamber_ids: 챔버 ID 문자열.
        lot_id: LOT ID(로트 ID).
        main_step: 메인 스텝.

    반환:
        "|" 구분자를 사용한 결합 문자열.

    부작용:
        없음. 순수 문자열 조합입니다.
    """

    # -----------------------------------------------------------------------------
    # 1) 입력 정규화 헬퍼
    # -----------------------------------------------------------------------------
    def _normalize(value: str | None) -> str:
        if value is None:
            return ""
        return str(value).strip()

    # -----------------------------------------------------------------------------
    # 2) 필드 결합
    # -----------------------------------------------------------------------------
    return "|".join(
        [
            _normalize(line_id),
            _normalize(eqp_id),
            _normalize(chamber_ids),
            _normalize(lot_id),
            _normalize(main_step),
        ]
    )


class DroneSOP(models.Model):
    """Drone SOP 관련 데이터(알림/상태/지라 연동 등)를 저장하는 모델입니다."""

    _LEGACY_DELIVERY_SEED_KEYS = {
        "send_jira",
        "send_messenger",
        "send_mail",
        "jira_reason",
        "messenger_reason",
        "mail_reason",
        "inform_step",
        "jira_key",
        "informed_at",
    }

    sop_key = models.CharField(max_length=300, unique=True)
    line_id = models.CharField(max_length=50, null=True, blank=True)
    sdwt_prod = models.CharField(max_length=64, null=True, blank=True)
    sample_type = models.CharField(max_length=50, null=True, blank=True)
    sample_group = models.CharField(max_length=50, null=True, blank=True)
    eqp_id = models.CharField(max_length=50, null=True, blank=True)
    chamber_ids = models.CharField(max_length=50, null=True, blank=True)
    lot_id = models.CharField(max_length=50, null=True, blank=True)
    proc_id = models.CharField(max_length=50, null=True, blank=True)
    ppid = models.CharField(max_length=50, null=True, blank=True)
    main_step = models.CharField(max_length=50, null=True, blank=True)
    metro_current_step = models.CharField(max_length=50, null=True, blank=True)
    metro_steps = models.CharField(max_length=1000, null=True, blank=True)
    metro_end_step = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)
    knox_id = models.CharField(max_length=50, null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    user_sdwt_prod = models.CharField(max_length=64, null=True, blank=True)
    target_user_sdwt_prod = models.CharField(max_length=64, null=True, blank=True)
    defect_url = models.TextField(null=True, blank=True)
    instant_inform = models.SmallIntegerField(default=0)
    needtosend = models.SmallIntegerField(default=1)
    custom_end_step = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())

    def __init__(self, *args: object, **kwargs: object) -> None:
        """legacy delivery 입력값을 runtime 호환 seed로 분리합니다."""

        legacy_seed = {
            key: kwargs.pop(key)
            for key in list(kwargs.keys())
            if key in self._LEGACY_DELIVERY_SEED_KEYS
        }
        super().__init__(*args, **kwargs)
        self._legacy_delivery_seed = legacy_seed

    class Meta:
        db_table = "drone_sop"
        indexes = [
            models.Index(fields=["sdwt_prod"], name="idx_dro_sop_sdw_prd"),
            models.Index(fields=["created_at", "id"], name="idx_dro_sop_crt_at_id"),
            models.Index(
                fields=["user_sdwt_prod", "created_at", "id"],
                name="idx_dro_sop_usr_sdw_prd_dd5e5",
            ),
            models.Index(
                fields=["target_user_sdwt_prod", "created_at", "id"],
                name="idx_dro_sop_tgt_crt_id",
            ),
        ]

    def __str__(self) -> str:  # 관리자/디버깅용 문자열 표현(커버리지 제외): pragma: no cover
        """관리자/디버깅용 문자열 표현을 반환합니다."""

        return f"SOP {self.line_id or '-'} {self.main_step or '-'}"

    def save(self, *args: object, **kwargs: object) -> None:
        """sop_key가 없으면 생성 후 저장합니다.

        부작용:
            DB 저장이 발생합니다.
        """

        # -------------------------------------------------------------------------
        # 1) sop_key 생성(없을 때만)
        # -------------------------------------------------------------------------
        if not self.sop_key:
            self.sop_key = build_sop_key(
                line_id=self.line_id,
                eqp_id=self.eqp_id,
                chamber_ids=self.chamber_ids,
                lot_id=self.lot_id,
                main_step=self.main_step,
            )
        # -------------------------------------------------------------------------
        # 2) 저장 호출
        # -------------------------------------------------------------------------
        super().save(*args, **kwargs)
        self._seed_legacy_delivery_rows()

    def _seed_legacy_delivery_rows(self) -> None:
        """legacy kwargs로 들어온 delivery 상태를 delivery row로 변환합니다."""

        seed = getattr(self, "_legacy_delivery_seed", None)
        if not isinstance(seed, dict) or not seed or not self.pk:
            return

        targets = self._resolve_legacy_delivery_seed_targets(seed=seed)
        if not targets:
            self._legacy_delivery_seed = {}
            return
        if not self.target_user_sdwt_prod:
            self.target_user_sdwt_prod = targets[0]
            type(self).objects.filter(pk=self.pk).update(target_user_sdwt_prod=targets[0])
        target_code = targets[0]
        target = DroneSopTarget.objects.filter(target_user_sdwt_prod__iexact=target_code).order_by("id").first()
        dispatch, _ = DroneSopTargetDispatch.objects.get_or_create(
            sop_id=int(self.pk),
            target_code_snapshot=target_code,
            defaults={
                "target": target,
                "target_display_snapshot": target_code,
                "resolution_status": "resolved",
                "dispatch_type": DroneSopTargetDispatch.DispatchTypes.AUTO,
                "status": DroneSopTargetDispatch.Statuses.PENDING,
            },
        )

        channel_specs = (
            (DroneSopDelivery.Channels.JIRA, "send_jira", "jira_reason"),
            (DroneSopDelivery.Channels.MESSENGER, "send_messenger", "messenger_reason"),
            (DroneSopDelivery.Channels.MAIL, "send_mail", "mail_reason"),
        )
        for channel, send_key, reason_key in channel_specs:
            raw_status = seed.get(send_key, 0)
            try:
                numeric_status = int(raw_status or 0)
            except (TypeError, ValueError):
                numeric_status = 0

            status = DroneSopDelivery.Statuses.PENDING
            reason = None
            external_key = None
            sent_at = None
            if numeric_status > 0:
                status = DroneSopDelivery.Statuses.SUCCESS
                sent_at = seed.get("informed_at")
                if channel == DroneSopDelivery.Channels.JIRA:
                    external_key = seed.get("jira_key")
            elif numeric_status < 0:
                status = DroneSopDelivery.Statuses.FAILED
                reason = seed.get(reason_key) or "send_failed"

            DroneSopDelivery.objects.update_or_create(
                dispatch=dispatch,
                channel=channel,
                defaults={
                    "sop_id": int(self.pk),
                    "status": status,
                    "reason": reason,
                    "external_key": external_key,
                    "sent_at": sent_at,
                    "sent_step": seed.get("inform_step"),
                },
            )
        self._legacy_delivery_seed = {}

    @staticmethod
    def _normalize_seed_text(value: object) -> str | None:
        """legacy seed 문자열을 공백 제거 기준으로 정규화합니다."""

        if not isinstance(value, str):
            return None
        cleaned = value.strip()
        return cleaned if cleaned else None

    def _resolve_legacy_delivery_seed_targets(self, *, seed: dict[str, object]) -> list[str]:
        """legacy target seed 또는 현재 매핑으로 delivery target을 해석합니다."""

        explicit_target = self._normalize_seed_text(self.target_user_sdwt_prod)
        if explicit_target:
            return [explicit_target]

        sdwt_prod = self._normalize_seed_text(self.sdwt_prod)
        user_sdwt_prod = self._normalize_seed_text(self.user_sdwt_prod)
        if sdwt_prod and user_sdwt_prod:
            pair_targets = list(
                DroneSopTargetMapping.objects.filter(sdwt_prod__iexact=sdwt_prod, user_sdwt_prod__iexact=user_sdwt_prod)
                .select_related("target")
                .exclude(target__target_user_sdwt_prod="")
                .values_list("target__target_user_sdwt_prod", flat=True)
                .order_by("id")
            )
            if pair_targets:
                return [target for target in pair_targets if isinstance(target, str) and target.strip()][:1]
        if sdwt_prod:
            sdwt_targets = list(
                DroneSopTargetMapping.objects.filter(sdwt_prod__iexact=sdwt_prod)
                .filter(Q(user_sdwt_prod__isnull=True) | Q(user_sdwt_prod=""))
                .select_related("target")
                .exclude(target__target_user_sdwt_prod="")
                .values_list("target__target_user_sdwt_prod", flat=True)
                .order_by("id")
            )
            if sdwt_targets:
                return [target for target in sdwt_targets if isinstance(target, str) and target.strip()][:1]
        if user_sdwt_prod:
            user_targets = list(
                DroneSopTargetMapping.objects.filter(user_sdwt_prod__iexact=user_sdwt_prod)
                .filter(Q(sdwt_prod__isnull=True) | Q(sdwt_prod=""))
                .select_related("target")
                .exclude(target__target_user_sdwt_prod="")
                .values_list("target__target_user_sdwt_prod", flat=True)
                .order_by("id")
            )
            if user_targets:
                return [target for target in user_targets if isinstance(target, str) and target.strip()][:1]
        fallback = user_sdwt_prod or sdwt_prod
        return [fallback] if fallback else []

    def _first_successful_jira_delivery(self) -> "DroneSopDelivery | None":
        """성공한 첫 번째 Jira delivery를 반환합니다."""

        if not self.pk:
            return None
        return (
            self.channel_deliveries.filter(
                channel=DroneSopDelivery.Channels.JIRA,
                status=DroneSopDelivery.Statuses.SUCCESS,
            )
            .order_by("id")
            .first()
        )

    @property
    def jira_key(self) -> str | None:
        """성공 Jira delivery의 외부 키를 표시용 속성으로 반환합니다."""

        delivery = self._first_successful_jira_delivery()
        return delivery.external_key if delivery else None

    @property
    def inform_step(self) -> str | None:
        """성공 Jira delivery의 발송 step을 표시용 속성으로 반환합니다."""

        delivery = self._first_successful_jira_delivery()
        return delivery.sent_step if delivery else None

    @property
    def informed_at(self):
        """성공 delivery의 최초 발송 시각을 표시용 속성으로 반환합니다."""

        if not self.pk:
            return None
        delivery = (
            self.channel_deliveries.filter(status=DroneSopDelivery.Statuses.SUCCESS)
            .order_by("sent_at", "id")
            .first()
        )
        return delivery.sent_at if delivery else None

    def _delivery_channel_rows(self, channel: str) -> list["DroneSopDelivery"]:
        """지정 채널의 delivery row를 ID 순서로 반환합니다."""

        return list(self.channel_deliveries.filter(channel=channel).order_by("id"))

    @staticmethod
    def _summarize_delivery_status(delivery_rows: list["DroneSopDelivery"]) -> tuple[int, str | None]:
        """delivery row 목록을 legacy 호환 상태값으로 요약합니다."""

        if not delivery_rows:
            return 0, None

        failed_reason = next(
            (
                row.reason
                for row in delivery_rows
                if row.status == DroneSopDelivery.Statuses.FAILED and row.reason
            ),
            None,
        )
        if failed_reason or any(row.status == DroneSopDelivery.Statuses.FAILED for row in delivery_rows):
            return -1, failed_reason
        if any(row.status == DroneSopDelivery.Statuses.PENDING for row in delivery_rows):
            return 0, None
        if any(row.status == DroneSopDelivery.Statuses.SUCCESS for row in delivery_rows):
            return 1, None
        disabled_reason = next((row.reason for row in delivery_rows if row.reason), None)
        return 0, disabled_reason

    def _delivery_status_value(self, channel: str) -> int:
        """지정 채널의 legacy 호환 상태값을 반환합니다."""

        status_value, _ = self._summarize_delivery_status(self._delivery_channel_rows(channel))
        return status_value

    def _delivery_reason_value(self, channel: str) -> str | None:
        """지정 채널의 legacy 호환 사유값을 반환합니다."""

        _, reason = self._summarize_delivery_status(self._delivery_channel_rows(channel))
        return reason

    @property
    def send_jira(self) -> int:
        """Jira delivery 상태를 legacy 호환 상태값으로 반환합니다."""

        return self._delivery_status_value(DroneSopDelivery.Channels.JIRA)

    @property
    def send_messenger(self) -> int:
        """메신저 delivery 상태를 legacy 호환 상태값으로 반환합니다."""

        return self._delivery_status_value(DroneSopDelivery.Channels.MESSENGER)

    @property
    def send_mail(self) -> int:
        """메일 delivery 상태를 legacy 호환 상태값으로 반환합니다."""

        return self._delivery_status_value(DroneSopDelivery.Channels.MAIL)

    @property
    def jira_reason(self) -> str | None:
        """Jira delivery 실패/비활성 사유를 legacy 호환 속성으로 반환합니다."""

        return self._delivery_reason_value(DroneSopDelivery.Channels.JIRA)

    @property
    def messenger_reason(self) -> str | None:
        """메신저 delivery 실패/비활성 사유를 legacy 호환 속성으로 반환합니다."""

        return self._delivery_reason_value(DroneSopDelivery.Channels.MESSENGER)

    @property
    def mail_reason(self) -> str | None:
        """메일 delivery 실패/비활성 사유를 legacy 호환 속성으로 반환합니다."""

        return self._delivery_reason_value(DroneSopDelivery.Channels.MAIL)




class DroneSopTarget(models.Model):
    """Drone SOP 알림 target 기준 채널 설정을 저장하는 모델입니다.

    target_user_sdwt_prod는 알림 묶음의 고유 식별자이며, line_id는 해당 target이
    어느 라인 설정 화면에서 관리되는지 나타내는 소유 라인입니다.
    """

    class Sources(models.TextChoices):
        AFFILIATION = "affiliation", "Affiliation"
        CUSTOM = "custom", "Custom"
        SYSTEM = "system", "System"

    target_user_sdwt_prod = models.CharField(max_length=64)
    line_id = models.CharField(max_length=50, blank=True, default="")
    jira_key = models.CharField(max_length=64, null=True, blank=True)
    chatroom_id = models.BigIntegerField(null=True, blank=True)
    jira_template_key = models.CharField(max_length=50, null=True, blank=True)
    mail_template_key = models.CharField(max_length=50, null=True, blank=True)
    messenger_template_key = models.CharField(max_length=50, null=True, blank=True)
    jira_enabled = models.BooleanField(default=True)
    messenger_enabled = models.BooleanField(default=True)
    mail_enabled = models.BooleanField(default=True)
    needtosend_comment_last_at = models.CharField(max_length=64, null=True, blank=True)
    needtosend_ignore_sample_type = models.BooleanField(default=False)
    needtosend_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())

    class Meta:
        db_table = "drone_sop_target"
        constraints = [
            models.UniqueConstraint(
                fields=["target_user_sdwt_prod"],
                name="uniq_dro_sop_target",
            ),
        ]
        indexes = [
            models.Index(fields=["line_id"], name="idx_dro_sop_tgt_line"),
        ]

    @classmethod
    def get_or_create_by_name(cls, *, target_user_sdwt_prod: str, line_id: str = "") -> "DroneSopTarget":
        """target 이름으로 target row를 조회하거나 생성합니다."""

        normalized = target_user_sdwt_prod.strip() if isinstance(target_user_sdwt_prod, str) else ""
        if not normalized:
            raise ValueError("target_user_sdwt_prod is required")
        existing = cls.objects.filter(target_user_sdwt_prod__iexact=normalized).order_by("id").first()
        if existing is not None:
            return existing
        try:
            target, _ = cls.objects.get_or_create(
                target_user_sdwt_prod=normalized,
                defaults={
                    "line_id": line_id,
                },
            )
            return target
        except IntegrityError:
            concurrent = cls.objects.filter(target_user_sdwt_prod__iexact=normalized).order_by("id").first()
            if concurrent is None:
                raise
            return concurrent

    def __str__(self) -> str:  # 관리자/디버깅용 문자열 표현(커버리지 제외): pragma: no cover
        """관리자/디버깅용 문자열 표현을 반환합니다."""

        chatroom_display = self.chatroom_id if self.chatroom_id is not None else "-"
        line_display = self.line_id or "-"
        return f"{line_display} / {self.target_user_sdwt_prod} (jira={self.jira_key or '-'}, msg={chatroom_display})"


class DroneSopTargetMapping(models.Model):
    """Drone SOP sdwt_prod/user_sdwt_prod 조합을 target으로 매핑하는 모델입니다."""

    sdwt_prod = models.CharField(max_length=64, null=True, blank=True)
    user_sdwt_prod = models.CharField(max_length=64, null=True, blank=True)
    target = models.ForeignKey(
        DroneSopTarget,
        on_delete=models.CASCADE,
        related_name="mappings",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())

    class Meta:
        db_table = "drone_sop_target_mapping"
        constraints = [
            models.CheckConstraint(
                check=(
                    (Q(sdwt_prod__isnull=False) & ~Q(sdwt_prod=""))
                    | (Q(user_sdwt_prod__isnull=False) & ~Q(user_sdwt_prod=""))
                ),
                name="chk_dro_sop_tgt_map_req",
            ),
            models.UniqueConstraint(
                Lower("sdwt_prod"),
                Lower("user_sdwt_prod"),
                name="uniq_dro_tgt_map_pair",
                condition=(
                    Q(sdwt_prod__isnull=False)
                    & ~Q(sdwt_prod="")
                    & Q(user_sdwt_prod__isnull=False)
                    & ~Q(user_sdwt_prod="")
                ),
            ),
            models.UniqueConstraint(
                Lower("sdwt_prod"),
                name="uniq_dro_tgt_map_sdw",
                condition=(
                    Q(sdwt_prod__isnull=False)
                    & ~Q(sdwt_prod="")
                    & (Q(user_sdwt_prod__isnull=True) | Q(user_sdwt_prod=""))
                ),
            ),
            models.UniqueConstraint(
                Lower("user_sdwt_prod"),
                name="uniq_dro_tgt_map_usr",
                condition=(
                    Q(user_sdwt_prod__isnull=False)
                    & ~Q(user_sdwt_prod="")
                    & (Q(sdwt_prod__isnull=True) | Q(sdwt_prod=""))
                ),
            ),
        ]

    @property
    def target_user_sdwt_prod(self) -> str:
        """연결된 target의 이름을 legacy 호환 속성으로 반환합니다."""

        return self.target.target_user_sdwt_prod

    def __str__(self) -> str:  # 관리자/디버깅용 문자열 표현(커버리지 제외): pragma: no cover
        """관리자/디버깅용 문자열 표현을 반환합니다."""

        return f"{self.sdwt_prod or '-'} / {self.user_sdwt_prod or '-'} -> {self.target_user_sdwt_prod}"


class DroneSopTargetRecipient(models.Model):
    """Drone SOP 채널별 실제 수신인 사용자를 저장하는 모델입니다.

    target의 소유 line_id와 채널 설정은 DroneSopTarget에서 관리합니다.
    """

    class Channels(models.TextChoices):
        MAIL = "mail", "Mail"
        MESSENGER = "messenger", "Messenger"

    target = models.ForeignKey(
        DroneSopTarget,
        on_delete=models.CASCADE,
        related_name="recipients",
    )
    channel = models.CharField(max_length=16, choices=Channels.choices)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="drone_sop_recipients",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())

    class Meta:
        db_table = "drone_sop_target_recipient"
        constraints = [
            models.UniqueConstraint(
                fields=["target", "channel", "user"],
                name="uniq_dro_sop_tgt_rcp_usr",
            ),
        ]
        indexes = [
            models.Index(
                fields=["target", "channel"],
                name="idx_dro_sop_tgt_rcp_tgt",
            ),
            models.Index(fields=["user"], name="idx_dro_sop_tgt_rcp_usr"),
        ]

    @property
    def target_user_sdwt_prod(self) -> str:
        """연결된 target의 이름을 legacy 호환 속성으로 반환합니다."""

        return self.target.target_user_sdwt_prod

    def __str__(self) -> str:  # 관리자/디버깅용 문자열 표현(커버리지 제외): pragma: no cover
        """관리자/디버깅용 문자열 표현을 반환합니다."""

        return f"{self.target_user_sdwt_prod} / {self.channel} / {self.user_id}"


class DroneSopTargetDispatch(models.Model):
    """Drone SOP와 target 1개를 묶은 발송 작업 단위입니다.

    DroneSOP는 POP3 upsert로 계속 갱신되는 현재 상태를 보관하고, 이 모델은
    화면/발송 기준의 target별 row 역할을 담당합니다.
    """

    class DispatchTypes(models.TextChoices):
        AUTO = "auto", "Auto"
        INSTANT = "instant", "Instant"
        MANUAL = "manual", "Manual"
        RETRY = "retry", "Retry"

    class Statuses(models.TextChoices):
        PENDING = "pending", "Pending"
        DISPATCHING = "dispatching", "Dispatching"
        SUCCESS = "success", "Success"
        PARTIAL_FAILED = "partial_failed", "Partial failed"
        FAILED = "failed", "Failed"
        DISABLED = "disabled", "Disabled"
        CANCELLED = "cancelled", "Cancelled"

    sop = models.ForeignKey(
        DroneSOP,
        on_delete=models.CASCADE,
        related_name="target_dispatches",
    )
    target = models.ForeignKey(
        DroneSopTarget,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sop_dispatches",
    )
    target_code_snapshot = models.CharField(max_length=64)
    target_display_snapshot = models.CharField(max_length=128, null=True, blank=True)
    resolution_status = models.CharField(max_length=32, default="resolved")
    dispatch_type = models.CharField(max_length=16, choices=DispatchTypes.choices, default=DispatchTypes.AUTO)
    status = models.CharField(max_length=24, choices=Statuses.choices, default=Statuses.PENDING)
    comment_override = models.TextField(null=True, blank=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="drone_sop_dispatch_requests",
    )
    requested_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())

    class Meta:
        db_table = "drone_sop_target_dispatch"
        constraints = [
            models.UniqueConstraint(
                fields=["sop", "target_code_snapshot"],
                name="uniq_dro_sop_tgt_dsp",
            ),
            models.CheckConstraint(
                condition=Q(
                    status__in=[
                        "pending",
                        "dispatching",
                        "success",
                        "partial_failed",
                        "failed",
                        "disabled",
                        "cancelled",
                    ]
                ),
                name="chk_dro_sop_tgt_dsp_st",
            ),
        ]
        indexes = [
            models.Index(fields=["sop", "status"], name="idx_dro_sop_tgt_dsp_sop"),
            models.Index(fields=["target_code_snapshot"], name="idx_dro_sop_tgt_dsp_cd"),
        ]

    def __str__(self) -> str:  # 관리자/디버깅용 문자열 표현(커버리지 제외): pragma: no cover
        """관리자/디버깅용 문자열 표현을 반환합니다."""

        return f"{self.sop_id} / {self.target_code_snapshot} / {self.status}"


class DroneSopDelivery(models.Model):
    """target dispatch별 channel 최종 발송 결과를 저장하는 모델입니다."""

    class Channels(models.TextChoices):
        JIRA = "jira", "Jira"
        MAIL = "mail", "Mail"
        MESSENGER = "messenger", "Messenger"

    class Statuses(models.TextChoices):
        PENDING = "pending", "Pending"
        SENDING = "sending", "Sending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        DISABLED = "disabled", "Disabled"
        CANCELLED = "cancelled", "Cancelled"

    sop = models.ForeignKey(
        DroneSOP,
        on_delete=models.CASCADE,
        related_name="channel_deliveries",
    )
    dispatch = models.ForeignKey(
        DroneSopTargetDispatch,
        on_delete=models.CASCADE,
        related_name="deliveries",
    )
    channel = models.CharField(max_length=16, choices=Channels.choices)
    status = models.CharField(max_length=16, choices=Statuses.choices, default=Statuses.PENDING)
    reason = models.CharField(max_length=64, null=True, blank=True)
    external_key = models.CharField(max_length=128, null=True, blank=True)
    sent_comment = models.TextField(null=True, blank=True)
    sent_step = models.CharField(max_length=50, null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    attempt_count = models.PositiveIntegerField(default=0)
    template_key_snapshot = models.CharField(max_length=50, null=True, blank=True)
    channel_config_snapshot = models.JSONField(null=True, blank=True)
    recipient_snapshot = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())

    class Meta:
        db_table = "drone_sop_delivery"
        constraints = [
            models.UniqueConstraint(
                fields=["dispatch", "channel"],
                name="uniq_dro_sop_dlv_dsp_ch",
            ),
            models.CheckConstraint(
                condition=Q(status__in=["pending", "sending", "success", "failed", "disabled", "cancelled"]),
                name="chk_dro_sop_dlv_sts",
            ),
        ]
        indexes = [
            models.Index(fields=["dispatch", "channel"], name="idx_dro_sop_dlv_dsp"),
            models.Index(fields=["sop", "channel"], name="idx_dro_sop_dlv_sop"),
            models.Index(fields=["channel", "status"], name="idx_dro_sop_dlv_sts"),
        ]

    def __str__(self) -> str:  # 관리자/디버깅용 문자열 표현(커버리지 제외): pragma: no cover
        """관리자/디버깅용 문자열 표현을 반환합니다."""

        return f"{self.sop_id} / {self.channel} / {self.status}"

    def save(self, *args: object, **kwargs: object) -> None:
        """legacy 직접 생성 경로에서 dispatch가 없으면 자동 보강합니다."""

        if not self.dispatch_id and self.sop_id:
            target_code = "__TARGET_MISSING__"
            if self.sop_id and getattr(self, "sop", None) is not None:
                target_code = (self.sop.target_user_sdwt_prod or "").strip() or target_code
            target = None
            if not target_code.startswith("__"):
                target = DroneSopTarget.objects.filter(target_user_sdwt_prod__iexact=target_code).order_by("id").first()
            dispatch, _ = DroneSopTargetDispatch.objects.get_or_create(
                sop_id=self.sop_id,
                target_code_snapshot=target_code,
                defaults={
                    "target": target,
                    "target_display_snapshot": target_code,
                    "resolution_status": "target_missing" if target_code.startswith("__") else "resolved",
                    "dispatch_type": DroneSopTargetDispatch.DispatchTypes.AUTO,
                    "status": DroneSopTargetDispatch.Statuses.PENDING,
                },
            )
            self.dispatch = dispatch
        super().save(*args, **kwargs)


class DroneSopDeliveryAttempt(models.Model):
    """Drone SOP delivery의 실제 외부 발송 시도 1회를 기록하는 모델입니다."""

    class Statuses(models.TextChoices):
        SENDING = "sending", "Sending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    delivery = models.ForeignKey(
        DroneSopDelivery,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    attempt_no = models.PositiveIntegerField()
    status = models.CharField(max_length=16, choices=Statuses.choices, default=Statuses.SENDING)
    sent_comment_snapshot = models.TextField(null=True, blank=True)
    sent_step_snapshot = models.CharField(max_length=50, null=True, blank=True)
    request_snapshot = models.JSONField(null=True, blank=True)
    response_snapshot = models.JSONField(null=True, blank=True)
    error_code = models.CharField(max_length=64, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())

    class Meta:
        db_table = "drone_sop_delivery_attempt"
        constraints = [
            models.UniqueConstraint(
                fields=["delivery", "attempt_no"],
                name="uniq_dro_sop_dlv_att_no",
            ),
            models.CheckConstraint(
                condition=Q(status__in=["sending", "success", "failed"]),
                name="chk_dro_sop_dlv_att_st",
            ),
        ]
        indexes = [
            models.Index(fields=["delivery", "attempt_no"], name="idx_dro_sop_dlv_att_dlv"),
            models.Index(fields=["status", "started_at"], name="idx_dro_sop_dlv_att_st"),
        ]

    def __str__(self) -> str:  # 관리자/디버깅용 문자열 표현(커버리지 제외): pragma: no cover
        """관리자/디버깅용 문자열 표현을 반환합니다."""

        return f"{self.delivery_id} / #{self.attempt_no} / {self.status}"


class DroneEarlyInform(models.Model):
    """Drone 조기 알림 설정(라인/스텝 기준)을 저장하는 모델입니다."""

    line_id = models.CharField(max_length=50)
    main_step = models.CharField(max_length=50)
    custom_end_step = models.CharField(max_length=50, null=True, blank=True)
    updated_by = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "drone_early_inform"
        constraints = [
            models.UniqueConstraint(
                fields=["line_id", "main_step"],
                name="uniq_dro_erl_inf_ln_id_mn_stp",
            )
        ]

    def __str__(self) -> str:  # 관리자/디버깅용 문자열 표현(커버리지 제외): pragma: no cover
        """관리자/디버깅용 문자열 표현을 반환합니다."""

        return f"{self.line_id} - {self.main_step}"


__all__ = [
    "DroneEarlyInform",
    "DroneSOP",
    "DroneSopDeliveryAttempt",
    "DroneSopDelivery",
    "DroneSopTarget",
    "DroneSopTargetDispatch",
    "DroneSopTargetMapping",
    "DroneSopTargetRecipient",
    "build_sop_key",
]
