"""station_master 적재 대상 및 처리 이력 모델입니다."""

from __future__ import annotations

from django.db import models
from django.db.models.functions import Now


class StationMaster(models.Model):
    """station_master 원천 데이터를 저장합니다."""

    area = models.CharField(max_length=40, null=True, blank=True)
    station = models.CharField(max_length=40, null=True, blank=True)
    station_lookup = models.CharField(max_length=40, null=True, blank=True)
    room = models.CharField(max_length=3, null=True, blank=True)
    module = models.CharField(max_length=2, null=True, blank=True)
    st_group = models.CharField(max_length=2, null=True, blank=True)
    machine_id = models.CharField(max_length=40, null=True, blank=True)
    machine_type = models.CharField(max_length=20, null=True, blank=True)
    status = models.CharField(max_length=2, null=True, blank=True)
    station_name = models.CharField(max_length=40, null=True, blank=True)
    ch_class = models.CharField(max_length=1, null=True, blank=True)
    ch_main = models.CharField(max_length=10, null=True, blank=True)
    status_desc = models.CharField(max_length=60, null=True, blank=True)
    bay = models.CharField(max_length=8, null=True, blank=True)
    sdwt_eng = models.CharField(max_length=40, null=True, blank=True)
    sdwt_eng2 = models.CharField(max_length=40, null=True, blank=True)
    sdwt_prod = models.CharField(max_length=50, null=True, blank=True)
    sdwt_prod_lookup = models.CharField(max_length=50, null=True, blank=True)
    del_flag = models.CharField(max_length=1, null=True, blank=True)
    machine_time = models.FloatField(null=True, blank=True)
    sbatch_size = models.FloatField(null=True, blank=True)
    c_flag = models.CharField(max_length=1, null=True, blank=True)
    c_run = models.FloatField(null=True, blank=True)
    c_idle = models.FloatField(null=True, blank=True)
    c_idle_rev = models.FloatField(null=True, blank=True)
    da_reason = models.CharField(max_length=2, null=True, blank=True)
    da_date = models.CharField(max_length=8, null=True, blank=True)
    zone = models.CharField(max_length=40, null=True, blank=True)
    block = models.CharField(max_length=40, null=True, blank=True)
    no_del_flag = models.CharField(max_length=1, null=True, blank=True)
    endfab_flag = models.CharField(max_length=1, null=True, blank=True)
    mfab_flag = models.CharField(max_length=40, null=True, blank=True)
    port_cnt = models.FloatField(null=True, blank=True)
    da_reason2 = models.CharField(max_length=2, null=True, blank=True)
    oht = models.CharField(max_length=1, null=True, blank=True)
    metro_grp = models.CharField(max_length=10, null=True, blank=True)
    prc_group = models.CharField(max_length=50, null=True, blank=True)
    prc_group_lookup = models.CharField(max_length=50, null=True, blank=True)
    scanner = models.CharField(max_length=40, null=True, blank=True)
    amhs = models.CharField(max_length=2, null=True, blank=True)
    chm_type = models.CharField(max_length=20, null=True, blank=True)
    fc_step = models.CharField(max_length=1, null=True, blank=True)
    close_day = models.CharField(max_length=8, null=True, blank=True)
    close_shift = models.CharField(max_length=1, null=True, blank=True)
    ad_flag = models.CharField(max_length=1, null=True, blank=True)
    en_reason = models.CharField(max_length=2, null=True, blank=True)
    dv_flag = models.CharField(max_length=1, null=True, blank=True)
    ed_reason = models.CharField(max_length=2, null=True, blank=True)
    in_line = models.CharField(max_length=5, null=True, blank=True)
    floor_line_id = models.CharField(max_length=40, null=True, blank=True)
    index_area = models.CharField(max_length=10, null=True, blank=True)
    dv_date = models.CharField(max_length=8, null=True, blank=True)
    purge_yn = models.CharField(max_length=1, null=True, blank=True)
    purge_target_yn = models.CharField(max_length=1, null=True, blank=True)
    addr_book_id = models.CharField(max_length=50, null=True, blank=True)
    eff_loss_type = models.CharField(max_length=40, null=True, blank=True)
    incld_reason_detail_code = models.CharField(max_length=40, null=True, blank=True)
    maker_name = models.CharField(max_length=120, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())

    class Meta:
        db_table = "station_master"
        indexes = [
            models.Index(fields=["sdwt_prod_lookup", "prc_group_lookup", "station"], name="idx_st_sdwt_prc_st"),
            models.Index(fields=["prc_group_lookup", "sdwt_prod_lookup", "station"], name="idx_st_prc_sdwt_st"),
            models.Index(fields=["station_lookup"], name="idx_st_station_lkp"),
            models.Index(fields=["floor_line_id"], name="idx_st_floor_ln"),
            models.Index(fields=["station"], name="idx_station_master_station"),
            models.Index(fields=["machine_id"], name="idx_station_master_mch"),
        ]

    def __str__(self) -> str:
        """관리자/디버깅용 문자열 표현을 반환합니다."""

        return f"station_master {self.station or '-'}"

    def save(self, *args: object, **kwargs: object) -> None:
        """조회용 정규화 키를 채운 뒤 저장합니다."""

        self.station_lookup = (self.station or "").strip().upper() or None
        self.sdwt_prod_lookup = (self.sdwt_prod or "").strip().upper() or None
        self.prc_group_lookup = (self.prc_group or "").strip().upper() or None
        super().save(*args, **kwargs)


class StationMasterLoadJob(models.Model):
    """station_master 파일 적재 처리 이력을 저장합니다."""

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
        db_table = "station_master_load_job"
        indexes = [
            models.Index(fields=["status"], name="idx_station_mst_job_sts"),
            models.Index(fields=["created_at"], name="idx_station_mst_job_crt"),
        ]

    def __str__(self) -> str:
        """관리자/디버깅용 문자열 표현을 반환합니다."""

        return f"{self.file_name} ({self.status})"
