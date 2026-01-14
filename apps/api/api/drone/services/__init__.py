# =============================================================================
# 모듈: 드론 서비스 파사드
# 주요 구성: early_inform/sop_pop3/sop_jira/utils
# 주요 가정: 외부에서는 api.drone.services를 통해 접근합니다.
# =============================================================================
"""드론 서비스 레이어 모듈입니다.

기능 영역별로 모듈을 분리했습니다:
 - 조기 알림 CRUD: `services/early_inform.py`
 - Drone SOP POP3 수집: `services/sop_pop3.py`
 - Drone SOP Jira 연동: `services/sop_jira.py`
 - Jira 템플릿/프로젝트 키 갱신: `services/jira_user_template.py`
 - 공통 유틸: `services/utils.py`

이 모듈은 안정적인 import 파사드 역할을 합니다(예: `from api.drone import services`).
"""

from __future__ import annotations

from .early_inform import (
    DroneEarlyInformDuplicateError,
    DroneEarlyInformNotFoundError,
    DroneEarlyInformUpdateResult,
    create_early_inform_entry,
    delete_early_inform_entry,
    update_early_inform_entry,
)
from .jira_user_template import upsert_drone_sop_jira_user_template
from .sop_jira import (
    DroneJiraConfig,
    DroneSopInstantInformResult,
    DroneSopJiraCreateResult,
    _jira_session,
    _update_drone_sop_jira_status,
    enqueue_drone_sop_jira_instant_inform,
    run_drone_sop_jira_create_from_env,
)
from .sop_pop3 import (
    DroneSopPop3Config,
    DroneSopPop3IngestResult,
    NeedToSendRule,
    _build_drone_sop_row,
    _upsert_drone_sop_rows,
    run_drone_sop_pop3_ingest_from_env,
)
from .utils import (
    _lock_key,
    _parse_bool,
    _parse_int,
    _release_advisory_lock,
    _try_advisory_lock,
)

__all__ = [
    "DroneEarlyInformDuplicateError",
    "DroneEarlyInformNotFoundError",
    "DroneEarlyInformUpdateResult",
    "DroneJiraConfig",
    "DroneSopInstantInformResult",
    "DroneSopJiraCreateResult",
    "DroneSopPop3Config",
    "DroneSopPop3IngestResult",
    "NeedToSendRule",
    "_build_drone_sop_row",
    "_jira_session",
    "_lock_key",
    "_parse_bool",
    "_parse_int",
    "_release_advisory_lock",
    "_try_advisory_lock",
    "_update_drone_sop_jira_status",
    "_upsert_drone_sop_rows",
    "create_early_inform_entry",
    "delete_early_inform_entry",
    "enqueue_drone_sop_jira_instant_inform",
    "run_drone_sop_jira_create_from_env",
    "run_drone_sop_pop3_ingest_from_env",
    "upsert_drone_sop_jira_user_template",
    "update_early_inform_entry",
]
