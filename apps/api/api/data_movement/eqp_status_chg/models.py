"""eqp_status_chg 적재 대상 및 처리 이력 모델입니다."""

from __future__ import annotations

from django.db import models
from django.db.models.functions import Now


class EqpStatusChg(models.Model):
    """EQP 상태 변경 이력을 timeline 조회용 최신 원천으로 저장합니다."""

    eqp_cb = models.CharField(max_length=41)
    eqp_cb_lookup = models.CharField(max_length=41, null=True, blank=True)
    line_id = models.CharField(max_length=8, null=True, blank=True)
    chg_time = models.DateTimeField()
    eqp_code = models.CharField(max_length=20, null=True, blank=True)
    eqp_mode_type = models.CharField(max_length=20, null=True, blank=True)
    eqp_status_type = models.CharField(max_length=10, null=True, blank=True)
    chg_comment = models.CharField(max_length=500, null=True, blank=True)
    operator_emp_id = models.CharField(max_length=25, null=True, blank=True)
    eqp_event_key = models.DecimalField(max_digits=38, decimal_places=0)
    last_update_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())

    class Meta:
        db_table = "eqp_status_chg"
        indexes = [
            models.Index(fields=["eqp_cb_lookup", "-chg_time"], name="idx_eqp_sts_lkp_tm"),
            models.Index(fields=["eqp_cb", "chg_time"], name="idx_eqp_sts_chg_cb_tm"),
            models.Index(fields=["chg_time"], name="idx_eqp_sts_chg_tm"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["eqp_event_key"], name="uniq_eqp_sts_chg_evt"),
        ]

    def __str__(self) -> str:
        """관리자/디버깅용 문자열 표현을 반환합니다."""

        return f"{self.eqp_cb} {self.chg_time:%Y-%m-%d %H:%M:%S}"

    def save(self, *args: object, **kwargs: object) -> None:
        """조회용 정규화 키를 채운 뒤 저장합니다."""

        self.eqp_cb_lookup = (self.eqp_cb or "").strip().upper() or None
        super().save(*args, **kwargs)


class EqpStatusChgLoadJob(models.Model):
    """eqp_status_chg 파일 적재 처리 이력을 저장합니다."""

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
        db_table = "eqp_status_chg_load_job"
        indexes = [
            models.Index(fields=["status"], name="idx_eqp_sts_chg_lj_sts"),
            models.Index(fields=["created_at"], name="idx_eqp_sts_chg_lj_crt"),
        ]

    def __str__(self) -> str:
        """관리자/디버깅용 문자열 표현을 반환합니다."""

        return f"{self.file_name} ({self.status})"
