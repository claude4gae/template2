"""eqp_status_chg 파일 적재 spec입니다."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings

TABLE_NAME = "eqp_status_chg"
TEMP_TABLE_NAME = "tmp_eqp_status_chg"
FILE_PATTERN = "*m_eqp_status_chg*.csv.deflate"
FILE_SEPARATOR = "`"
RETENTION_DAYS = 180
UPSERT_KEY = "eqp_event_key"

DEFAULT_TABLE_DIR = Path(settings.DATA_MOVEMENT_EQP_STATUS_CHG_DIR)

FILE_COLUMNS = [
    "eqp_id",
    "line_id",
    "chamber_id",
    "chg_time",
    "eqp_code",
    "eqp_mode_type",
    "eqp_status_type",
    "chg_comment",
    "operator_emp_id",
    "eqp_event_key",
    "last_update_time",
]

DB_COLUMNS = [
    "eqp_cb",
    "eqp_cb_lookup",
    "line_id",
    "chg_time",
    "eqp_code",
    "eqp_mode_type",
    "eqp_status_type",
    "chg_comment",
    "operator_emp_id",
    "eqp_event_key",
    "last_update_time",
]
