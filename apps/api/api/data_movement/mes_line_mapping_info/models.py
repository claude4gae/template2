"""mes_line_mapping_info 적재 대상 및 처리 이력 모델입니다."""

from __future__ import annotations

from django.db import models
from django.db.models.functions import Now


class MesLineMappingInfo(models.Model):
    """MES line 매핑 원천 데이터를 저장합니다."""

    seq_no = models.FloatField(null=True, blank=True)
    line_id = models.CharField(max_length=40, null=True, blank=True)
    mos_line_id = models.CharField(max_length=40, null=True, blank=True)
    fdc_line_id = models.CharField(max_length=40, null=True, blank=True)
    gpm_line_name = models.TextField(null=True, blank=True)
    gpm_line_name_lookup = models.TextField(null=True, blank=True)
    oi_line_name = models.CharField(max_length=40, null=True, blank=True)
    msg_line_id = models.CharField(max_length=40, null=True, blank=True)
    mcs_line_id = models.CharField(max_length=40, null=True, blank=True)
    line_full_name = models.CharField(max_length=100, null=True, blank=True)
    line_abbr_name = models.CharField(max_length=100, null=True, blank=True)
    gbm_name = models.CharField(max_length=40, null=True, blank=True)
    site_id = models.CharField(max_length=40, null=True, blank=True)
    district_name = models.CharField(max_length=40, null=True, blank=True)
    inch_vals = models.CharField(max_length=40, null=True, blank=True)
    area_class_type = models.CharField(max_length=50, null=True, blank=True)
    fab_type = models.CharField(max_length=40, null=True, blank=True)
    cdc_user_id = models.CharField(max_length=40, null=True, blank=True)
    fdc_db_user_id = models.CharField(max_length=50, null=True, blank=True)
    mos_eaihub_line_id = models.CharField(max_length=40, null=True, blank=True)
    mos_db_line_name = models.CharField(max_length=40, null=True, blank=True)
    sort_seq = models.FloatField(null=True, blank=True)
    use_yn = models.CharField(max_length=1, null=True, blank=True)
    del_yn = models.CharField(max_length=1, null=True, blank=True)
    create_date = models.DateTimeField(null=True, blank=True)
    create_user_id = models.CharField(max_length=40, null=True, blank=True)
    update_date = models.DateTimeField(null=True, blank=True)
    update_user_id = models.CharField(max_length=40, null=True, blank=True)
    rms_line_id = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())

    class Meta:
        db_table = "mes_line_mapping_info"
        indexes = [
            models.Index(fields=["gpm_line_name_lookup", "gbm_name", "use_yn", "del_yn"], name="idx_mes_gpm_flg"),
            models.Index(fields=["msg_line_id", "gbm_name", "use_yn", "del_yn"], name="idx_mes_msg_flg"),
            models.Index(fields=["line_id"], name="idx_mes_line_map_line"),
            models.Index(fields=["msg_line_id"], name="idx_mes_line_map_msg"),
            models.Index(fields=["gpm_line_name"], name="idx_mes_line_map_gpm"),
            models.Index(fields=["gbm_name", "use_yn", "del_yn"], name="idx_mes_line_map_flg"),
        ]

    def __str__(self) -> str:
        """관리자/디버깅용 문자열 표현을 반환합니다."""

        return f"mes_line_mapping_info {self.line_id or '-'}"

    def save(self, *args: object, **kwargs: object) -> None:
        """조회용 정규화 키를 채운 뒤 저장합니다."""

        self.gpm_line_name_lookup = (self.gpm_line_name or "").strip().upper() or None
        super().save(*args, **kwargs)


class MesLineMappingInfoLoadJob(models.Model):
    """mes_line_mapping_info 파일 적재 처리 이력을 저장합니다."""

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
        db_table = "mes_line_mapping_info_load_job"
        indexes = [
            models.Index(fields=["status"], name="idx_mes_line_map_job_sts"),
            models.Index(fields=["created_at"], name="idx_mes_line_map_job_crt"),
        ]

    def __str__(self) -> str:
        """관리자/디버깅용 문자열 표현을 반환합니다."""

        return f"{self.file_name} ({self.status})"
