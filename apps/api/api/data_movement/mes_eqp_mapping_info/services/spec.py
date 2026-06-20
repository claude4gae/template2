"""mes_eqp_mapping_info 파일 적재 spec입니다."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings

TABLE_NAME = "mes_eqp_mapping_info"
TEMP_TABLE_NAME = "tmp_mes_eqp_mapping_info"
FILE_PATTERN = "*_MES_MAPPING_INFO_*.csv.deflate"
FILE_SEPARATOR = "`"
REPLACE_SCOPE = "all"

DEFAULT_TABLE_DIR = Path(settings.DATA_MOVEMENT_MES_EQP_MAPPING_INFO_DIR)

COLUMNS = [
    "eqp_id",
    "line_id",
    "mos_line_id",
    "fdc_line_id",
    "gpm_line_name",
    "oi_line_name",
    "msg_line_id",
    "mcs_line_id",
    "main_eqp_id",
    "chamber_id",
    "fdc_eqp_index_no",
    "fdc_unit_index_no",
    "fdc_unit_id",
    "fdc_unit_disp_name",
    "fdc_eqp_unit_type",
    "smdm_eqp_key_no",
    "gpm_room_name",
    "gpm_eqp_model_name",
    "fdc_eqp_model_name",
    "fdc_model_name",
    "sdwt_name",
    "eqp_type",
    "insert_date",
    "update_date",
]

DATETIME_COLUMNS = [
    "insert_date",
    "update_date",
]

FLOAT_COLUMNS = [
    "fdc_eqp_index_no",
    "fdc_unit_index_no",
]
