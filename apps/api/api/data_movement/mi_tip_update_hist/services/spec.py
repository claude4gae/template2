"""mi_tip_update_hist 파일 적재 spec입니다."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings

TABLE_NAME = "mi_tip_update_hist"
TEMP_TABLE_NAME = "tmp_mi_tip_update_hist"
FILE_PATTERN = "*MI_TIP_UPDATE_HIST*.csv.deflate"
FILE_SEPARATOR = "`"
RETENTION_DAYS = 180
UPSERT_KEY = "tip_event_key"

DEFAULT_TABLE_DIR = Path(settings.DATA_MOVEMENT_MI_TIP_UPDATE_HIST_DIR)

LEVEL_MAPPING = {
    "PREVENT/TIP_OCCUR/LEVEL1": "L1_TIP",
    "PREVENT/TIP_RELEASE/LEVEL1": "L1_CNT",
    "DOING/TIP_RELEASE/LEVEL1": "DOING",
    "PREVENT/TIP_OCCUR/LEVEL2": "L2_TIP",
    "PREVENT/TIP_RELEASE/LEVEL2": "L2_CNT",
    "PREVENT/TIP_OCCUR/LEVEL3": "L3_TIP",
    "PREVENT/TIP_RELEASE/LEVEL3": "L3_CNT",
}

FILE_COLUMNS = [
    "line_id",
    "eqp_id",
    "step_seq",
    "process_id",
    "ppid",
    "tip_chamber_id",
    "reticle_id",
    "product_id",
    "sum_time",
    "rule_pkg_update_date",
    "gpm_update_date",
    "register_name",
    "tip_type",
    "tip_chg_type",
    "tip_level",
    "tip_comment",
    "tkin_restrc_lot_count",
    "cur_tkin_lot_count",
    "term_intlk_occur_time",
    "last_update_date",
]

DB_COLUMNS = [
    "tip_event_key",
    "line_id",
    "eqp_cb",
    "eqp_cb_lookup",
    "step_seq",
    "process_id",
    "ppid",
    "reticle_id",
    "product_id",
    "sum_time",
    "rule_pkg_update_date",
    "gpm_update_date",
    "register_name",
    "event_type",
    "tip_type",
    "tip_chg_type",
    "tip_level",
    "tip_comment",
    "tkin_restrc_lot_count",
    "cur_tkin_lot_count",
    "term_intlk_occur_time",
    "last_update_date",
]
