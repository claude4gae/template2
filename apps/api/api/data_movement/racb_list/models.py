"""racb_list 적재 대상 및 처리 이력 모델입니다."""

from __future__ import annotations

from django.db import models
from django.db.models.functions import Now


class RacbList(models.Model):
    """RACB 이력을 timeline 조회용 내부 원천으로 저장합니다."""

    c_racb_id = models.TextField()
    o_racb_id = models.TextField(null=True, blank=True)
    gbm = models.TextField(null=True, blank=True)
    line = models.TextField(null=True, blank=True)
    line_id = models.TextField(null=True, blank=True)
    area = models.TextField(null=True, blank=True)
    sdwt_name = models.TextField(null=True, blank=True)
    title = models.TextField(null=True, blank=True)
    sub_title = models.TextField(null=True, blank=True)
    fiveone = models.TextField(null=True, blank=True)
    racb_type_cd = models.TextField(null=True, blank=True)
    major_category = models.TextField(null=True, blank=True)
    minor_category = models.TextField(null=True, blank=True)
    eqp_cb = models.TextField()
    eqp_cb_lookup = models.TextField(null=True, blank=True)
    prc_groups = models.TextField(null=True, blank=True)
    level_data = models.TextField(null=True, blank=True)
    status_code = models.TextField(null=True, blank=True)
    status = models.TextField(null=True, blank=True)
    detail_type_cd = models.TextField(null=True, blank=True)
    change_cd = models.TextField(null=True, blank=True)
    fdc = models.TextField(null=True, blank=True)
    npw = models.TextField(null=True, blank=True)
    metro = models.TextField(null=True, blank=True)
    defect = models.TextField(null=True, blank=True)
    create_date = models.DateTimeField()
    due_date = models.DateTimeField(null=True, blank=True)
    user_name = models.TextField(null=True, blank=True)
    create_user = models.TextField(null=True, blank=True)
    update_date = models.DateTimeField()
    update_user = models.TextField(null=True, blank=True)
    sub_area = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())

    class Meta:
        db_table = "racb_list"
        indexes = [
            models.Index(fields=["eqp_cb_lookup", "-update_date"], name="idx_racb_lkp_dt"),
            models.Index(fields=["eqp_cb", "update_date"], name="idx_racb_list_cb_upd"),
            models.Index(fields=["update_date"], name="idx_racb_list_upd"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["c_racb_id", "eqp_cb"], name="uniq_racb_list_id_cb"),
        ]

    def __str__(self) -> str:
        """관리자/디버깅용 문자열 표현을 반환합니다."""

        return f"{self.c_racb_id} {self.eqp_cb}"

    def save(self, *args: object, **kwargs: object) -> None:
        """조회용 정규화 키를 채운 뒤 저장합니다."""

        self.eqp_cb_lookup = (self.eqp_cb or "").strip().upper() or None
        super().save(*args, **kwargs)


class RacbListLoadJob(models.Model):
    """racb_list 파일 적재 처리 이력을 저장합니다."""

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
        db_table = "racb_list_load_job"
        indexes = [
            models.Index(fields=["status"], name="idx_racb_list_lj_sts"),
            models.Index(fields=["created_at"], name="idx_racb_list_lj_crt"),
        ]

    def __str__(self) -> str:
        """관리자/디버깅용 문자열 표현을 반환합니다."""

        return f"{self.file_name} ({self.status})"
