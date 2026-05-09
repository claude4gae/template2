# =============================================================================
# 모듈: 드론 SOP/조기 알림 모델
# 주요 구성: DroneSOP, DroneSopTarget, DroneSopDelivery, DroneEarlyInform
# 주요 가정: sop_key는 필드 조합으로 생성합니다.
# =============================================================================
from __future__ import annotations

from django.conf import settings
from django.db import IntegrityError, models
from django.db.models import Q
from django.db.models.functions import Lower, Now


def _rewrite_target_lookup_key(key: str) -> str:
    """legacy target_user_sdwt_prod lookup을 target FK lookup으로 변환합니다."""

    if key == "target_user_sdwt_prod":
        return "target__target_user_sdwt_prod"
    if key.startswith("target_user_sdwt_prod__"):
        return f"target__target_user_sdwt_prod__{key.split('__', 1)[1]}"
    return key


class TargetLookupQuerySet(models.QuerySet):
    """target FK 전환 중 legacy target lookup을 흡수하는 QuerySet입니다."""

    def _rewrite_kwargs(self, kwargs: dict[str, object]) -> dict[str, object]:
        """target_user_sdwt_prod lookup kwargs를 target FK lookup으로 변환합니다."""

        return {_rewrite_target_lookup_key(key): value for key, value in kwargs.items()}

    def filter(self, *args: object, **kwargs: object):
        """legacy target lookup을 지원하는 filter입니다."""

        return super().filter(*args, **self._rewrite_kwargs(kwargs))

    def exclude(self, *args: object, **kwargs: object):
        """legacy target lookup을 지원하는 exclude입니다."""

        return super().exclude(*args, **self._rewrite_kwargs(kwargs))

    def get(self, *args: object, **kwargs: object):
        """legacy target lookup을 지원하는 get입니다."""

        return super().get(*args, **self._rewrite_kwargs(kwargs))

    def order_by(self, *field_names: str):
        """legacy target 정렬 컬럼을 target FK 정렬로 변환합니다."""

        rewritten = []
        for field_name in field_names:
            prefix = "-" if field_name.startswith("-") else ""
            raw_name = field_name[1:] if prefix else field_name
            rewritten.append(f"{prefix}{_rewrite_target_lookup_key(raw_name)}")
        return super().order_by(*rewritten)

    def values_list(self, *fields: str, **kwargs: object):
        """legacy target values_list 컬럼을 target FK 컬럼으로 변환합니다."""

        rewritten = [_rewrite_target_lookup_key(field) for field in fields]
        return super().values_list(*rewritten, **kwargs)


class TargetLookupManager(models.Manager.from_queryset(TargetLookupQuerySet)):
    """target FK 전환 호환 Manager입니다."""


class LegacyTargetNameMixin:
    """legacy target_user_sdwt_prod 생성 인자를 target FK로 변환하는 mixin입니다."""

    _legacy_target_user_sdwt_prod: str | None

    def __init__(self, *args: object, **kwargs: object) -> None:
        """legacy target_user_sdwt_prod kwarg를 저장 후 기본 초기화를 수행합니다."""

        legacy_target = kwargs.pop("target_user_sdwt_prod", None)
        super().__init__(*args, **kwargs)
        self._legacy_target_user_sdwt_prod = legacy_target if isinstance(legacy_target, str) else None

    def _ensure_target_from_legacy_name(self) -> None:
        """target FK가 없고 legacy target 값이 있으면 target row를 연결합니다."""

        if getattr(self, "target_id", None):
            return
        target_name = (self._legacy_target_user_sdwt_prod or "").strip()
        if not target_name:
            return
        self.target = DroneSopTarget.get_or_create_by_name(target_user_sdwt_prod=target_name)

    def save(self, *args: object, **kwargs: object) -> None:
        """저장 전에 legacy target 값을 target FK로 변환합니다."""

        self._ensure_target_from_legacy_name()
        super().save(*args, **kwargs)


class DroneSopTargetManager(models.Manager):
    """비활성 placeholder target만 명시 생성 호출로 승격하는 Manager입니다."""

    def create(self, **kwargs: object):
        """동일 target이 이미 활성 상태면 중복 생성을 거부합니다."""

        target_name = kwargs.get("target_user_sdwt_prod")
        normalized = target_name.strip() if isinstance(target_name, str) else ""
        if not normalized:
            return super().create(**kwargs)

        existing = self.filter(target_user_sdwt_prod__iexact=normalized).order_by("id").first()
        if existing is None:
            return super().create(**kwargs)
        if existing.is_active:
            raise IntegrityError("duplicate target_user_sdwt_prod")

        update_fields: list[str] = []
        for field_name, value in kwargs.items():
            if field_name == "target_user_sdwt_prod" or not hasattr(existing, field_name):
                continue
            if getattr(existing, field_name) != value:
                setattr(existing, field_name, value)
                update_fields.append(field_name)

        next_is_active = kwargs.get("is_active", True)
        if bool(next_is_active) and not existing.is_active:
            existing.is_active = True
            update_fields.append("is_active")
        if update_fields:
            existing.save(update_fields=[*update_fields, "updated_at"])
        return existing


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
        "target_user_sdwt_prod",
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
        constraints = [
            models.UniqueConstraint(
                fields=["line_id", "eqp_id", "chamber_ids", "lot_id", "main_step"],
                name="uniq_dro_sop_ln_id_eqp_i_92d25",
            )
        ]
        indexes = [
            models.Index(fields=["sdwt_prod"], name="idx_dro_sop_sdw_prd"),
            models.Index(fields=["created_at", "id"], name="idx_dro_sop_crt_at_id"),
            models.Index(
                fields=["user_sdwt_prod", "created_at", "id"],
                name="idx_dro_sop_usr_sdw_prd_dd5e5",
            ),
            models.Index(fields=["knox_id"], name="idx_dro_sop_knx_id"),
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

        channel_specs = (
            (DroneSopChannelDelivery.Channels.JIRA, "send_jira", "jira_reason"),
            (DroneSopChannelDelivery.Channels.MESSENGER, "send_messenger", "messenger_reason"),
            (DroneSopChannelDelivery.Channels.MAIL, "send_mail", "mail_reason"),
        )
        for channel, send_key, reason_key in channel_specs:
            raw_status = seed.get(send_key, 0)
            try:
                numeric_status = int(raw_status or 0)
            except (TypeError, ValueError):
                numeric_status = 0

            status = DroneSopChannelDelivery.Statuses.PENDING
            reason = None
            external_key = None
            sent_at = None
            if numeric_status > 0:
                status = DroneSopChannelDelivery.Statuses.SUCCESS
                sent_at = seed.get("informed_at")
                if channel == DroneSopChannelDelivery.Channels.JIRA:
                    external_key = seed.get("jira_key")
            elif numeric_status < 0:
                status = DroneSopChannelDelivery.Statuses.FAILED
                reason = seed.get(reason_key) or "send_failed"

            for target in targets:
                DroneSopChannelDelivery.objects.update_or_create(
                    sop_id=int(self.pk),
                    target=DroneSopTarget.get_or_create_by_name(target_user_sdwt_prod=target),
                    channel=channel,
                    defaults={
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

        explicit_target = self._normalize_seed_text(seed.get("target_user_sdwt_prod"))
        if explicit_target:
            return [explicit_target]

        sdwt_prod = self._normalize_seed_text(self.sdwt_prod)
        user_sdwt_prod = self._normalize_seed_text(self.user_sdwt_prod)
        if sdwt_prod and user_sdwt_prod:
            pair_targets = list(
                DroneSopTargetMapping.objects.filter(
                    is_active=True,
                    sdwt_prod__iexact=sdwt_prod,
                    user_sdwt_prod__iexact=user_sdwt_prod,
                )
                .select_related("target")
                .exclude(target__target_user_sdwt_prod="")
                .values_list("target__target_user_sdwt_prod", flat=True)
                .order_by("id")
            )
            if pair_targets:
                return [target for target in pair_targets if isinstance(target, str) and target.strip()][:1]
        if sdwt_prod:
            sdwt_targets = list(
                DroneSopTargetMapping.objects.filter(
                    is_active=True,
                    sdwt_prod__iexact=sdwt_prod,
                )
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
                DroneSopTargetMapping.objects.filter(
                    is_active=True,
                    user_sdwt_prod__iexact=user_sdwt_prod,
                )
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

    def _delivery_channel_rows(self, channel: str) -> list["DroneSopChannelDelivery"]:
        """지정 채널의 delivery row를 ID 순서로 반환합니다."""

        return list(self.channel_deliveries.filter(channel=channel).order_by("id"))

    @staticmethod
    def _summarize_delivery_status(delivery_rows: list["DroneSopChannelDelivery"]) -> tuple[int, str | None]:
        """delivery row 목록을 legacy 호환 상태값으로 요약합니다."""

        if not delivery_rows:
            return 0, None

        failed_reason = next(
            (
                row.reason
                for row in delivery_rows
                if row.status == DroneSopChannelDelivery.Statuses.FAILED and row.reason
            ),
            None,
        )
        if failed_reason or any(row.status == DroneSopChannelDelivery.Statuses.FAILED for row in delivery_rows):
            return -1, failed_reason
        if any(row.status == DroneSopChannelDelivery.Statuses.PENDING for row in delivery_rows):
            return 0, None
        if any(row.status == DroneSopChannelDelivery.Statuses.SUCCESS for row in delivery_rows):
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
    def target_user_sdwt_prod(self) -> str | None:
        """첫 번째 delivery target을 legacy 호환 속성으로 반환합니다."""

        for delivery in self.channel_deliveries.order_by("id"):
            target = str(delivery.target_user_sdwt_prod or "").strip()
            if target and not target.startswith("__"):
                return target
        return None

    @property
    def send_jira(self) -> int:
        """Jira delivery 상태를 legacy 호환 상태값으로 반환합니다."""

        return self._delivery_status_value(DroneSopChannelDelivery.Channels.JIRA)

    @property
    def send_messenger(self) -> int:
        """메신저 delivery 상태를 legacy 호환 상태값으로 반환합니다."""

        return self._delivery_status_value(DroneSopChannelDelivery.Channels.MESSENGER)

    @property
    def send_mail(self) -> int:
        """메일 delivery 상태를 legacy 호환 상태값으로 반환합니다."""

        return self._delivery_status_value(DroneSopChannelDelivery.Channels.MAIL)

    @property
    def jira_reason(self) -> str | None:
        """Jira delivery 실패/비활성 사유를 legacy 호환 속성으로 반환합니다."""

        return self._delivery_reason_value(DroneSopChannelDelivery.Channels.JIRA)

    @property
    def messenger_reason(self) -> str | None:
        """메신저 delivery 실패/비활성 사유를 legacy 호환 속성으로 반환합니다."""

        return self._delivery_reason_value(DroneSopChannelDelivery.Channels.MESSENGER)

    @property
    def mail_reason(self) -> str | None:
        """메일 delivery 실패/비활성 사유를 legacy 호환 속성으로 반환합니다."""

        return self._delivery_reason_value(DroneSopChannelDelivery.Channels.MAIL)




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
    source = models.CharField(max_length=20, choices=Sources.choices, default=Sources.CUSTOM)
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
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_drone_sop_notification_targets",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())

    objects = DroneSopTargetManager()

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
                    "source": cls.Sources.SYSTEM if normalized.startswith("__") else cls.Sources.CUSTOM,
                    "is_active": False,
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


class DroneSopTargetMapping(LegacyTargetNameMixin, models.Model):
    """Drone SOP sdwt_prod/user_sdwt_prod 조합을 target으로 매핑하는 모델입니다."""

    sdwt_prod = models.CharField(max_length=64, null=True, blank=True)
    user_sdwt_prod = models.CharField(max_length=64, null=True, blank=True)
    target = models.ForeignKey(
        DroneSopTarget,
        on_delete=models.CASCADE,
        related_name="mappings",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())

    objects = TargetLookupManager()

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
                name="uniq_dro_tgt_map_pair_act",
                condition=(
                    Q(sdwt_prod__isnull=False)
                    & ~Q(sdwt_prod="")
                    & Q(user_sdwt_prod__isnull=False)
                    & ~Q(user_sdwt_prod="")
                    & Q(is_active=True)
                ),
            ),
            models.UniqueConstraint(
                Lower("sdwt_prod"),
                name="uniq_dro_tgt_map_sdw_act",
                condition=(
                    Q(sdwt_prod__isnull=False)
                    & ~Q(sdwt_prod="")
                    & (Q(user_sdwt_prod__isnull=True) | Q(user_sdwt_prod=""))
                    & Q(is_active=True)
                ),
            ),
            models.UniqueConstraint(
                Lower("user_sdwt_prod"),
                name="uniq_dro_tgt_map_usr_act",
                condition=(
                    Q(user_sdwt_prod__isnull=False)
                    & ~Q(user_sdwt_prod="")
                    & (Q(sdwt_prod__isnull=True) | Q(sdwt_prod=""))
                    & Q(is_active=True)
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


class DroneSopTargetRecipient(LegacyTargetNameMixin, models.Model):
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
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_drone_sop_recipients",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())

    objects = TargetLookupManager()

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


class DroneSopDelivery(LegacyTargetNameMixin, models.Model):
    """Drone SOP별 target/channel 발송 결과를 저장하는 모델입니다."""

    class Channels(models.TextChoices):
        JIRA = "jira", "Jira"
        MAIL = "mail", "Mail"
        MESSENGER = "messenger", "Messenger"

    class Statuses(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        DISABLED = "disabled", "Disabled"

    sop = models.ForeignKey(
        DroneSOP,
        on_delete=models.CASCADE,
        related_name="channel_deliveries",
    )
    target = models.ForeignKey(
        DroneSopTarget,
        on_delete=models.PROTECT,
        related_name="deliveries",
    )
    channel = models.CharField(max_length=16, choices=Channels.choices)
    status = models.CharField(max_length=16, choices=Statuses.choices, default=Statuses.PENDING)
    reason = models.CharField(max_length=64, null=True, blank=True)
    external_key = models.CharField(max_length=128, null=True, blank=True)
    sent_step = models.CharField(max_length=50, null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())

    objects = TargetLookupManager()

    class Meta:
        db_table = "drone_sop_delivery"
        constraints = [
            models.UniqueConstraint(
                fields=["sop", "target", "channel"],
                name="uniq_dro_sop_delivery",
            ),
        ]
        indexes = [
            models.Index(fields=["sop", "channel"], name="idx_dro_sop_dlv_sop"),
            models.Index(
                fields=["target", "channel", "status"],
                name="idx_dro_sop_dlv_tgt",
            ),
            models.Index(fields=["channel", "status"], name="idx_dro_sop_dlv_sts"),
        ]

    @property
    def target_user_sdwt_prod(self) -> str:
        """연결된 target의 이름을 legacy 호환 속성으로 반환합니다."""

        return self.target.target_user_sdwt_prod

    def __str__(self) -> str:  # 관리자/디버깅용 문자열 표현(커버리지 제외): pragma: no cover
        """관리자/디버깅용 문자열 표현을 반환합니다."""

        return f"{self.sop_id} / {self.target_user_sdwt_prod} / {self.channel} / {self.status}"


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


DroneSopUserSdwtChannel = DroneSopTarget
DroneSopUserSdwtProdMap = DroneSopTargetMapping
DroneSopChannelRecipient = DroneSopTargetRecipient
DroneSopChannelDelivery = DroneSopDelivery


__all__ = [
    "DroneEarlyInform",
    "DroneSOP",
    "DroneSopDelivery",
    "DroneSopTarget",
    "DroneSopTargetMapping",
    "DroneSopTargetRecipient",
    "DroneSopChannelDelivery",
    "DroneSopChannelRecipient",
    "DroneSopUserSdwtChannel",
    "DroneSopUserSdwtProdMap",
    "build_sop_key",
]
