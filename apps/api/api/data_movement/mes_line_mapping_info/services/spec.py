"""mes_line_mapping_info 파일 적재 spec입니다."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings

TABLE_NAME = "mes_line_mapping_info"
TEMP_TABLE_NAME = "tmp_mes_line_mapping_info"
FILE_PATTERN = "*_MES_MAPPING_INFO_*.csv.deflate"
FILE_SEPARATOR = "`"
REPLACE_SCOPE = "all"

DEFAULT_TABLE_DIR = Path(settings.DATA_MOVEMENT_MES_LINE_MAPPING_INFO_DIR)

COLUMNS = [
    "seq_no",
    "line_id",
    "mos_line_id",
    "fdc_line_id",
    "gpm_line_name",
    "oi_line_name",
    "msg_line_id",
    "mcs_line_id",
    "line_full_name",
    "line_abbr_name",
    "gbm_name",
    "site_id",
    "district_name",
    "inch_vals",
    "area_class_type",
    "fab_type",
    "cdc_user_id",
    "fdc_db_user_id",
    "mos_eaihub_line_id",
    "mos_db_line_name",
    "sort_seq",
    "use_yn",
    "del_yn",
    "create_date",
    "create_user_id",
    "update_date",
    "update_user_id",
    "rms_line_id",
]

DATETIME_COLUMNS = [
    "create_date",
    "update_date",
]

FLOAT_COLUMNS = [
    "seq_no",
    "sort_seq",
]
