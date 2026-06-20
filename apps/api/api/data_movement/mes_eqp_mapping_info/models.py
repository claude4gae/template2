"""mes_eqp_mapping_info 적재 대상 및 처리 이력 모델입니다."""

from __future__ import annotations

from django.db import models
from django.db.models.functions import Now


class MesEqpMappingInfo(models.Model):
    """MES 설비/라인 매핑 원천 데이터를 저장합니다."""

    eqp_id = models.CharField(max_length=40, null=True, blank=True)
    line_id = models.CharField(max_length=40, null=True, blank=True)
    mos_line_id = models.CharField(max_length=40, null=True, blank=True)
    fdc_line_id = models.CharField(max_length=40, null=True, blank=True)
    gpm_line_name = models.CharField(max_length=40, null=True, blank=True)
    oi_line_name = models.CharField(max_length=40, null=True, blank=True)
    msg_line_id = models.CharField(max_length=40, null=True, blank=True)
    mcs_line_id = models.CharField(max_length=40, null=True, blank=True)
    main_eqp_id = models.CharField(max_length=40, null=True, blank=True)
    chamber_id = models.CharField(max_length=40, null=True, blank=True)
    fdc_eqp_index_no = models.FloatField(null=True, blank=True)
    fdc_unit_index_no = models.FloatField(null=True, blank=True)
    fdc_unit_id = models.CharField(max_length=40, null=True, blank=True)
    fdc_unit_disp_name = models.CharField(max_length=40, null=True, blank=True)
    fdc_eqp_unit_type = models.CharField(max_length=100, null=True, blank=True)
    smdm_eqp_key_no = models.CharField(max_length=40, null=True, blank=True)
    gpm_room_name = models.CharField(max_length=40, null=True, blank=True)
    gpm_eqp_model_name = models.CharField(max_length=100, null=True, blank=True)
    fdc_eqp_model_name = models.CharField(max_length=100, null=True, blank=True)
    fdc_model_name = models.CharField(max_length=100, null=True, blank=True)
    sdwt_name = models.CharField(max_length=500, null=True, blank=True)
    eqp_type = models.CharField(max_length=40, null=True, blank=True)
    insert_date = models.DateTimeField(null=True, blank=True)
    update_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())

    class Meta:
        db_table = "mes_eqp_mapping_info"
        indexes = [
            models.Index(fields=["eqp_id"], name="idx_mes_eqp_map_eqp"),
            models.Index(fields=["line_id"], name="idx_mes_eqp_map_line"),
        ]

    def __str__(self) -> str:
        """관리자/디버깅용 문자열 표현을 반환합니다."""

        return f"mes_eqp_mapping_info {self.eqp_id or '-'}"


class MesEqpMappingInfoLoadJob(models.Model):
    """mes_eqp_mapping_info 파일 적재 처리 이력을 저장합니다."""

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
        db_table = "mes_eqp_mapping_info_load_job"
        indexes = [
            models.Index(fields=["status"], name="idx_mes_eqp_map_job_sts"),
            models.Index(fields=["created_at"], name="idx_mes_eqp_map_job_crt"),
        ]

    def __str__(self) -> str:
        """관리자/디버깅용 문자열 표현을 반환합니다."""

        return f"{self.file_name} ({self.status})"
