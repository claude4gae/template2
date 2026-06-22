"""mi_tip_update_hist 적재 대상 및 처리 이력 모델입니다."""

from __future__ import annotations

from django.db import models
from django.db.models.functions import Now


class MiTipUpdateHist(models.Model):
    """TIP 이력을 timeline 조회용 내부 원천으로 저장합니다."""

    tip_event_key = models.CharField(max_length=32)
    line_id = models.CharField(max_length=10, null=True, blank=True)
    eqp_cb = models.CharField(max_length=65)
    eqp_cb_lookup = models.CharField(max_length=65, null=True, blank=True)
    step_seq = models.CharField(max_length=16, null=True, blank=True)
    process_id = models.CharField(max_length=16, null=True, blank=True)
    ppid = models.CharField(max_length=40, null=True, blank=True)
    reticle_id = models.CharField(max_length=30, null=True, blank=True)
    product_id = models.CharField(max_length=40, null=True, blank=True)
    sum_time = models.CharField(max_length=15, null=True, blank=True)
    rule_pkg_update_date = models.DateTimeField(null=True, blank=True)
    gpm_update_date = models.DateTimeField()
    register_name = models.CharField(max_length=40, null=True, blank=True)
    event_type = models.CharField(max_length=40, null=True, blank=True)
    tip_type = models.CharField(max_length=40, null=True, blank=True)
    tip_chg_type = models.CharField(max_length=40, null=True, blank=True)
    tip_level = models.CharField(max_length=16, null=True, blank=True)
    tip_comment = models.CharField(max_length=255, null=True, blank=True)
    tkin_restrc_lot_count = models.DecimalField(max_digits=38, decimal_places=0, null=True, blank=True)
    cur_tkin_lot_count = models.DecimalField(max_digits=38, decimal_places=0, null=True, blank=True)
    term_intlk_occur_time = models.CharField(max_length=18, null=True, blank=True)
    last_update_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())

    class Meta:
        db_table = "mi_tip_update_hist"
        indexes = [
            models.Index(fields=["eqp_cb_lookup", "-gpm_update_date"], name="idx_mi_tip_lkp_dt"),
            models.Index(fields=["eqp_cb", "gpm_update_date"], name="idx_mi_tip_upd_hist_cb_dt"),
            models.Index(fields=["gpm_update_date"], name="idx_mi_tip_upd_hist_dt"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["tip_event_key"], name="uniq_mi_tip_upd_hist_evt"),
        ]

    def __str__(self) -> str:
        """관리자/디버깅용 문자열 표현을 반환합니다."""

        return f"{self.eqp_cb} {self.gpm_update_date:%Y-%m-%d %H:%M:%S}"

    def save(self, *args: object, **kwargs: object) -> None:
        """조회용 정규화 키를 채운 뒤 저장합니다."""

        self.eqp_cb_lookup = (self.eqp_cb or "").strip().upper() or None
        super().save(*args, **kwargs)


class MiTipUpdateHistLoadJob(models.Model):
    """mi_tip_update_hist 파일 적재 처리 이력을 저장합니다."""

    class Status(models.TextChoices):
        """파일 적재 상태 값입니다."""

        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        DRY_RUN = "dry_run", "Dry run"

    file_name = models.TextField()
    file_path = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.RUNNING)
    row_count = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())

    class Meta:
        db_table = "mi_tip_update_hist_load_job"
        indexes = [
            models.Index(fields=["status"], name="idx_mi_tip_upd_hist_lj_sts"),
            models.Index(fields=["created_at"], name="idx_mi_tip_upd_hist_lj_crt"),
        ]

    def __str__(self) -> str:
        """관리자/디버깅용 문자열 표현을 반환합니다."""

        return f"{self.file_name} ({self.status})"
