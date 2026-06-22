"""station_master 파일 적재 spec입니다."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings

TABLE_NAME = "station_master"
TEMP_TABLE_NAME = "tmp_station_master"
FILE_PATTERN = "*_STATION_MASTER_*.csv.deflate"
FILE_SEPARATOR = "`"
REPLACE_SCOPE = "all"

DEFAULT_TABLE_DIR = Path(settings.DATA_MOVEMENT_STATION_MASTER_DIR)

COLUMNS = [
    "area",
    "station",
    "room",
    "module",
    "st_group",
    "machine_id",
    "machine_type",
    "status",
    "station_name",
    "ch_class",
    "ch_main",
    "status_desc",
    "bay",
    "sdwt_eng",
    "sdwt_eng2",
    "sdwt_prod",
    "del_flag",
    "machine_time",
    "sbatch_size",
    "c_flag",
    "c_run",
    "c_idle",
    "c_idle_rev",
    "da_reason",
    "da_date",
    "zone",
    "block",
    "no_del_flag",
    "endfab_flag",
    "mfab_flag",
    "port_cnt",
    "da_reason2",
    "oht",
    "metro_grp",
    "prc_group",
    "scanner",
    "amhs",
    "chm_type",
    "fc_step",
    "close_day",
    "close_shift",
    "ad_flag",
    "en_reason",
    "dv_flag",
    "ed_reason",
    "in_line",
    "floor_line_id",
    "index_area",
    "dv_date",
    "purge_yn",
    "purge_target_yn",
    "addr_book_id",
    "eff_loss_type",
    "incld_reason_detail_code",
    "maker_name",
]

DATETIME_COLUMNS = []

FLOAT_COLUMNS = [
    "machine_time",
    "sbatch_size",
    "c_run",
    "c_idle",
    "c_idle_rev",
    "port_cnt",
]
