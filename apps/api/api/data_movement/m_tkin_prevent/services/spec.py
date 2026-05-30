"""m_tkin_prevent 파일 적재 spec입니다."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings

TABLE_NAME = "m_tkin_prevent"
TEMP_TABLE_NAME = "tmp_m_tkin_prevent"
FILE_PATTERN = "*.csv.deflate"
REPLACE_COLUMN = "line_id"

DEFAULT_TABLE_DIR = Path(settings.DATA_MOVEMENT_M_TKIN_PREVENT_DIR)

COLUMNS = [
    "operator_name",
    "tkin_prevent_comment",
    "ppid",
    "registration_date",
    "registration_level",
    "fa_object2",
    "line_id",
    "tkin_prevent_type",
    "tkin_restrc_lot_count",
    "last_update_date",
    "process_id",
    "tkin_lot_count",
    "step_seq",
    "metro_lot_count",
    "reticle_id",
    "metro_step",
    "product_id",
    "reg_dept_name",
    "update_date",
    "eqp_id",
    "tkin_prevent_chamber_id",
    "schedule_priority",
    "photo_comment",
    "level2_comment",
    "level2_restrc_lot_count",
    "term_intlk_count",
    "term_intlk_hour",
    "tip_code",
    "expo_time",
    "check_time",
    "term1_residual_time",
    "check_time2",
    "term2_residual_time",
    "last_tkout_time",
    "first_intlk_time",
    "tkin_time",
    "term_intlk_group_type",
    "focus_value",
    "prev_rels_level",
    "data_chg_type",
    "level2_chk_cnt",
    "sample_group_vals",
    "auto_tip_rels_type",
    "seq_order_no",
    "cd_type",
    "rels_group_desc",
    "pm_reset_yn",
    "rsc_code",
    "rsc_chk_mins",
    "base_focus_spec",
]

DATETIME_COLUMNS = [
    "registration_date",
    "last_update_date",
    "update_date",
]

FLOAT_COLUMNS = [
    "tkin_restrc_lot_count",
    "tkin_lot_count",
    "metro_lot_count",
    "level2_restrc_lot_count",
    "check_time",
    "term1_residual_time",
    "check_time2",
    "term2_residual_time",
    "level2_chk_cnt",
    "seq_order_no",
]
