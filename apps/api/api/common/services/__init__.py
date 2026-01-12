# =============================================================================
# 모듈 설명: 공용 서비스/헬퍼의 공개 파사드를 제공합니다.
# - 주요 대상: 상수, 유틸, DB 헬퍼, 스토리지, 미들웨어
# - 불변 조건: 외부 모듈은 이 파사드를 통해 공용 기능을 사용합니다.
# =============================================================================

"""공용 서비스 모듈의 공개 파사드.

- 주요 대상: 공용 상수/유틸/DB 헬퍼/스토리지/미들웨어
- 주요 엔드포인트/클래스: ActivityLoggingMiddleware, KnoxIdRequiredMiddleware 등
- 가정/불변 조건: 공용 로직은 여기에서 일관되게 노출됨
"""
from __future__ import annotations

from .activity_logging import (
    merge_activity_metadata,
    set_activity_new_state,
    set_activity_previous_state,
    set_activity_summary,
)
from .affiliations import (
    UNKNOWN,
    UNASSIGNED_USER_SDWT_PROD,
    UNCLASSIFIED_USER_SDWT_PROD,
)
from .constants import (
    DATE_COLUMN_CANDIDATES,
    DATE_ONLY_REGEX,
    DEFAULT_TABLE,
    DIMENSION_CANDIDATES,
    LINE_SDWT_TABLE_NAME,
    MAX_FIELD_LENGTH,
    SAFE_IDENTIFIER,
)
from .date_helpers import (
    build_date_range_filters,
    ensure_date_bounds,
)
from .db import execute, get_cursor, run_query
from .db_utils import (
    build_line_filters,
    find_column,
    pick_base_timestamp_column,
    resolve_table_schema,
    TableSchema,
)
from .middleware import ActivityLoggingMiddleware, KnoxIdRequiredMiddleware
from .normalization import (
    normalize_date_only,
    normalize_line_id,
    normalize_text,
    sanitize_identifier,
    to_int,
)
from .request_helpers import (
    ensure_airflow_token,
    extract_bearer_token,
    parse_json_body,
    resolve_frontend_target,
)
from .storage import (
    delete_object,
    download_bytes,
    ensure_minio_bucket,
    get_minio_client,
    upload_bytes,
)

__all__ = [
    "ActivityLoggingMiddleware",
    "DATE_COLUMN_CANDIDATES",
    "DATE_ONLY_REGEX",
    "DEFAULT_TABLE",
    "DIMENSION_CANDIDATES",
    "KnoxIdRequiredMiddleware",
    "LINE_SDWT_TABLE_NAME",
    "MAX_FIELD_LENGTH",
    "SAFE_IDENTIFIER",
    "TableSchema",
    "UNKNOWN",
    "UNASSIGNED_USER_SDWT_PROD",
    "UNCLASSIFIED_USER_SDWT_PROD",
    "build_date_range_filters",
    "build_line_filters",
    "delete_object",
    "download_bytes",
    "ensure_airflow_token",
    "ensure_date_bounds",
    "ensure_minio_bucket",
    "execute",
    "extract_bearer_token",
    "find_column",
    "get_cursor",
    "get_minio_client",
    "merge_activity_metadata",
    "normalize_date_only",
    "normalize_line_id",
    "normalize_text",
    "parse_json_body",
    "pick_base_timestamp_column",
    "resolve_frontend_target",
    "resolve_table_schema",
    "run_query",
    "sanitize_identifier",
    "set_activity_new_state",
    "set_activity_previous_state",
    "set_activity_summary",
    "to_int",
    "upload_bytes",
]
