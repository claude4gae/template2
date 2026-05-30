"""ctttm_workorder_list 파일 적재 spec입니다."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings

TABLE_NAME = "ctttm_workorder_list"
TEMP_TABLE_NAME = "tmp_ctttm_workorder_list"
FILE_PATTERN = "*CT_*_WORKORDER_*.csv.deflate"
SOURCE_FILE_PATTERN = r"^(?:\d+_)?CT_(?P<source>MNU|MST)_WORKORDER_(?P<file_timestamp>\d{8}_\d{4})\.csv\.deflate$"
REPLACE_COLUMN = "source_type"
FILE_SEPARATOR = "\x03"
DEFAULT_TABLE_DIR = Path(settings.DATA_MOVEMENT_CTTTM_WORKORDER_LIST_DIR)

FILE_COLUMNS = [
    "workorder_id",
    "line_id",
    "jp_no",
    "seqpm_seq",
    "pm_no",
    "description",
    "asset",
    "event_date",
    "work_type",
    "status",
    "status_chg_date",
    "area_name",
    "inprg_date",
    "comp_date",
    "qual_cnt",
    "psgr_id",
    "mat_model",
    "close_date",
    "work_start_date",
    "work_end_date",
    "ems_status_issue_date",
    "pm_start_date",
    "in_tttm_yn",
    "reinprg_seq",
    "mat_wappr_date",
    "mat_appr_date",
    "mat_inprg_date",
    "mat_qual_date",
    "mat_comp_date",
    "mat_close_date",
    "dirty_type",
    "create_date",
    "create_user",
    "update_date",
    "update_user",
    "use_yn",
    "mat_status",
    "data_in_total",
    "data_in_current",
    "data_in_process",
    "data_in_status",
    "report_status",
    "mat_cre_dt",
    "site_id",
    "pm_type",
    "if_status",
    "if_update_user",
    "if_update_date",
    "related_workorder_id",
    "related_line_id",
    "related_update_user",
    "related_update_date",
    "max_comment_date",
    "sendfab_mail_batch_yn",
    "pbu_detail_yn",
]

DB_COLUMNS = [
    "workorder_id",
    "line_id",
    "eqp_id",
    "work_type",
    "description",
    "inprg_date",
    "comp_date",
]

COLUMN_SOURCES = {
    "eqp_id": "asset",
}

ROW_FILTERS = {
    "area_name": "ETCH",
}

CREATE_DATE_FILTER_COLUMN = "create_date"
CREATE_DATE_LOOKBACK_DAYS = 180
