"""racb_list 파일 적재 spec입니다."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings

TABLE_NAME = "racb_list"
TEMP_TABLE_NAME = "tmp_racb_list"
FILE_PATTERN = "*racb_list*.csv.deflate"
FILE_SEPARATOR = "`"

DEFAULT_TABLE_DIR = Path(settings.DATA_MOVEMENT_RACB_LIST_DIR)

FILE_COLUMNS = [
    "c_racb_id",
    "o_racb_id",
    "gbm",
    "line",
    "line_id",
    "area",
    "sdwt_name",
    "title",
    "sub_title",
    "fiveone",
    "racb_type_cd",
    "major_category",
    "minor_category",
    "eqp_ids",
    "prc_groups",
    "level_data",
    "status_code",
    "status",
    "detail_type_cd",
    "change_cd",
    "fdc",
    "npw",
    "metro",
    "defect",
    "create_date",
    "due_date",
    "user_name",
    "create_user",
    "update_date",
    "update_user",
    "sub_area",
]

DB_COLUMNS = [
    "c_racb_id",
    "o_racb_id",
    "gbm",
    "line",
    "line_id",
    "area",
    "sdwt_name",
    "title",
    "sub_title",
    "fiveone",
    "racb_type_cd",
    "major_category",
    "minor_category",
    "eqp_cb",
    "eqp_cb_lookup",
    "prc_groups",
    "level_data",
    "status_code",
    "status",
    "detail_type_cd",
    "change_cd",
    "fdc",
    "npw",
    "metro",
    "defect",
    "create_date",
    "due_date",
    "user_name",
    "create_user",
    "update_date",
    "update_user",
    "sub_area",
]
