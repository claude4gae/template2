# =============================================================================
# 모듈 설명: timeline 더미 데이터 셀렉터를 제공합니다.
# - 주요 함수: list_lines, list_sdwt_for_line, get_merged_logs 등
# - 불변 조건: 더미 데이터만 반환하며 DB 조회는 없습니다.
# =============================================================================

from __future__ import annotations

from typing import Dict, List, Tuple

# =============================================================================
# 상수: 더미 라인/설비/로그 데이터
# =============================================================================

LINE_LIST: List[Dict[str, str]] = [
    {"id": "LINE-A", "name": "Line A"},
    {"id": "LINE-B", "name": "Line B"},
]

SDWT_MAP: Dict[str, List[Dict[str, str]]] = {
    "LINE-A": [
        {"id": "SD-10", "name": "SDWT-10"},
    ],
    "LINE-B": [
        {"id": "SD-20", "name": "SDWT-20"},
    ],
}

PRC_GROUPS: Dict[Tuple[str, str], List[Dict[str, str]]] = {
    ("LINE-A", "SD-10"): [
        {"id": "ETCH", "name": "PRC Group - Etch"},
        {"id": "CVD", "name": "PRC Group - CVD"},
    ],
    ("LINE-B", "SD-20"): [
        {"id": "TEST", "name": "PRC Group - Test"},
    ],
}

EQUIPMENTS: Dict[Tuple[str, str, str], List[Dict[str, str]]] = {
    ("LINE-A", "SD-10", "ETCH"): [
        {"id": "EQP-ALPHA", "name": "ALPHA-ETCH-01"},
        {"id": "EQP-BRAVO", "name": "BRAVO-ETCH-02"},
    ],
    ("LINE-A", "SD-10", "CVD"): [
        {"id": "EQP-CVD-01", "name": "CVD-LINEA-01"},
    ],
    ("LINE-B", "SD-20", "TEST"): [
        {"id": "EQP-TEST-01", "name": "TEST-HANDLER-01"},
    ],
}

EQUIPMENT_INFO: Dict[str, Dict[str, str]] = {
    "EQP-ALPHA": {
        "id": "EQP-ALPHA",
        "name": "ALPHA-ETCH-01",
        "lineId": "LINE-A",
        "sdwtId": "SD-10",
        "prcGroup": "ETCH",
    },
    "EQP-BRAVO": {
        "id": "EQP-BRAVO",
        "name": "BRAVO-ETCH-02",
        "lineId": "LINE-A",
        "sdwtId": "SD-10",
        "prcGroup": "ETCH",
    },
    "EQP-CVD-01": {
        "id": "EQP-CVD-01",
        "name": "CVD-LINEA-01",
        "lineId": "LINE-A",
        "sdwtId": "SD-10",
        "prcGroup": "CVD",
    },
    "EQP-TEST-01": {
        "id": "EQP-TEST-01",
        "name": "TEST-HANDLER-01",
        "lineId": "LINE-B",
        "sdwtId": "SD-20",
        "prcGroup": "TEST",
    },
}

LOGS: Dict[str, Dict[str, List[Dict[str, object]]]] = {
    "EQP-ALPHA": {
        "eqp": [
            {
                "id": "EQP-ALPHA-001",
                "logType": "EQP",
                "eventType": "RUN",
                "eventTime": "2024-07-15T00:30:00Z",
                "endTime": "2024-07-15T02:30:00Z",
                "operator": "system",
                "comment": "Shift warm-up",
                "lineId": "LINE-A",
                "eqpId": "EQP-ALPHA",
            },
            {
                "id": "EQP-ALPHA-002",
                "logType": "EQP",
                "eventType": "DOWN",
                "eventTime": "2024-07-15T02:30:00Z",
                "endTime": "2024-07-15T03:30:00Z",
                "operator": "ops1",
                "comment": "Vacuum low",
                "lineId": "LINE-A",
                "eqpId": "EQP-ALPHA",
            },
            {
                "id": "EQP-ALPHA-003",
                "logType": "EQP",
                "eventType": "PM",
                "eventTime": "2024-07-15T03:30:00Z",
                "endTime": "2024-07-15T04:30:00Z",
                "operator": "maintenance",
                "comment": "Chamber clean",
                "lineId": "LINE-A",
                "eqpId": "EQP-ALPHA",
            },
            {
                "id": "EQP-ALPHA-004",
                "logType": "EQP",
                "eventType": "IDLE",
                "eventTime": "2024-07-15T04:30:00Z",
                "endTime": "2024-07-15T05:30:00Z",
                "operator": "ops1",
                "comment": "Waiting for lot",
                "lineId": "LINE-A",
                "eqpId": "EQP-ALPHA",
            },
            {
                "id": "EQP-ALPHA-005",
                "logType": "EQP",
                "eventType": "RUN",
                "eventTime": "2024-07-15T05:30:00Z",
                "endTime": "2024-07-15T08:30:00Z",
                "operator": "system",
                "comment": "Lot processing",
                "lineId": "LINE-A",
                "eqpId": "EQP-ALPHA",
            },
        ],
        "tip": [
            {
                "id": "TIP-ALPHA-001",
                "logType": "TIP",
                "eventType": "OPEN",
                "eventTime": "2024-07-15T01:00:00Z",
                "operator": "kim",
                "level": "MAJOR",
                "comment": "Opened chamber for clean",
                "url": "https://example.local/tip/TIP-ALPHA-001",
                "lineId": "LINE-A",
                "eqpId": "EQP-ALPHA",
                "process": "ETCH",
                "step": "STRIP",
                "ppid": "ALP-STRIP-01",
            },
            {
                "id": "TIP-ALPHA-002",
                "logType": "TIP",
                "eventType": "CLOSE",
                "eventTime": "2024-07-15T02:15:00Z",
                "operator": "kim",
                "level": "INFO",
                "comment": "Close after wipe down",
                "url": "https://example.local/tip/TIP-ALPHA-002",
                "lineId": "LINE-A",
                "eqpId": "EQP-ALPHA",
                "process": "ETCH",
                "step": "STRIP",
                "ppid": "ALP-STRIP-01",
            },
            {
                "id": "TIP-ALPHA-003",
                "logType": "TIP",
                "eventType": "OPEN",
                "eventTime": "2024-07-15T06:00:00Z",
                "operator": "lee",
                "level": "INFO",
                "comment": "Recipe load for pilot lot",
                "url": "https://example.local/tip/TIP-ALPHA-003",
                "lineId": "LINE-A",
                "eqpId": "EQP-ALPHA",
                "process": "ETCH",
                "step": "MAIN",
                "ppid": "ALP-ETCH-05",
            },
            {
                "id": "TIP-ALPHA-004",
                "logType": "TIP",
                "eventType": "CLOSE",
                "eventTime": "2024-07-15T07:45:00Z",
                "operator": "lee",
                "level": "MINOR",
                "comment": "Recipe completed",
                "url": "https://example.local/tip/TIP-ALPHA-004",
                "lineId": "LINE-A",
                "eqpId": "EQP-ALPHA",
                "process": "ETCH",
                "step": "MAIN",
                "ppid": "ALP-ETCH-05",
            },
        ],
        "ctttm": [
            {
                "id": "CTTTM-ALPHA-001",
                "logType": "CTTTM",
                "eventType": "CBM",
                "eventTime": "2024-07-15T03:45:00Z",
                "operator": "kim",
                "recipe": "ALP-ETCH-05",
                "comment": "Cycle time trending high",
                "duration": 12.5,
                "lineId": "LINE-A",
                "eqpId": "EQP-ALPHA",
            },
            {
                "id": "CTTTM-ALPHA-002",
                "logType": "CTTTM",
                "eventType": "NSP",
                "eventTime": "2024-07-15T07:15:00Z",
                "operator": "lee",
                "recipe": "ALP-ETCH-05",
                "comment": "Exceeded target time",
                "duration": 18.2,
                "lineId": "LINE-A",
                "eqpId": "EQP-ALPHA",
            },
        ],
        "racb": [
            {
                "id": "RACB-ALPHA-001",
                "logType": "RACB",
                "eventType": "WARN",
                "eventTime": "2024-07-15T04:05:00Z",
                "operator": "monitor",
                "comment": "Carrier slowed near load port",
                "url": "https://example.local/racb/RACB-ALPHA-001",
                "lineId": "LINE-A",
                "eqpId": "EQP-ALPHA",
            },
            {
                "id": "RACB-ALPHA-002",
                "logType": "RACB",
                "eventType": "ALARM",
                "eventTime": "2024-07-15T08:05:00Z",
                "operator": "monitor",
                "comment": "Carrier collision",
                "url": "https://example.local/racb/RACB-ALPHA-002",
                "lineId": "LINE-A",
                "eqpId": "EQP-ALPHA",
            },
        ],
        "jira": [
            {
                "id": "JIRA-ALPHA-001",
                "logType": "JIRA",
                "eventType": "CREATE",
                "eventTime": "2024-07-15T05:30:00Z",
                "operator": "ops1",
                "comment": "Opened investigation ticket",
                "url": "https://jira.local/browse/OPS-100",
                "lineId": "LINE-A",
                "eqpId": "EQP-ALPHA",
            }
        ],
        "event": [],
    },
    "EQP-BRAVO": {
        "eqp": [
            {
                "id": "EQP-BRAVO-001",
                "logType": "EQP",
                "eventType": "RUN",
                "eventTime": "2024-07-15T00:45:00Z",
                "endTime": "2024-07-15T02:15:00Z",
                "operator": "system",
                "comment": "Lot processing",
                "lineId": "LINE-A",
                "eqpId": "EQP-BRAVO",
            },
            {
                "id": "EQP-BRAVO-002",
                "logType": "EQP",
                "eventType": "DOWN",
                "eventTime": "2024-07-15T02:15:00Z",
                "endTime": "2024-07-15T03:45:00Z",
                "operator": "ops2",
                "comment": "Pressure alarm",
                "lineId": "LINE-A",
                "eqpId": "EQP-BRAVO",
            },
        ],
        "tip": [],
        "ctttm": [],
        "racb": [],
        "jira": [],
        "event": [],
    },
    "EQP-CVD-01": {
        "eqp": [
            {
                "id": "EQP-CVD-01-001",
                "logType": "EQP",
                "eventType": "RUN",
                "eventTime": "2024-07-15T01:10:00Z",
                "endTime": "2024-07-15T03:10:00Z",
                "operator": "system",
                "comment": "Recipe CVD-LINEA-01",
                "lineId": "LINE-A",
                "eqpId": "EQP-CVD-01",
            },
            {
                "id": "EQP-CVD-01-002",
                "logType": "EQP",
                "eventType": "PM",
                "eventTime": "2024-07-15T04:10:00Z",
                "endTime": "2024-07-15T05:30:00Z",
                "operator": "maintenance",
                "comment": "Chamber clean",
                "lineId": "LINE-A",
                "eqpId": "EQP-CVD-01",
            },
        ],
        "tip": [],
        "ctttm": [],
        "racb": [],
        "jira": [],
        "event": [],
    },
    "EQP-TEST-01": {
        "eqp": [
            {
                "id": "EQP-TEST-01-001",
                "logType": "EQP",
                "eventType": "RUN",
                "eventTime": "2024-07-15T02:00:00Z",
                "endTime": "2024-07-15T04:00:00Z",
                "operator": "system",
                "comment": "Handler cycle",
                "lineId": "LINE-B",
                "eqpId": "EQP-TEST-01",
            }
        ],
        "tip": [],
        "ctttm": [],
        "racb": [],
        "jira": [],
        "event": [],
    },
}


def normalize_id(value: str | None) -> str:
    """입력 ID를 공백 제거 후 대문자로 정규화합니다.

    입력:
    - value: 원본 ID(None 허용)

    반환:
    - str: 정규화된 ID(없으면 빈 문자열)

    부작용:
    - 없음

    오류:
    - 없음
    """

    return (value or "").strip().upper()


def _clone_items(items: List[Dict[str, object]]) -> List[Dict[str, object]]:
    """더미 항목 리스트를 얕은 복사해 반환합니다.

    입력:
    - items: 원본 항목 리스트

    반환:
    - List[Dict[str, object]]: 복사된 항목 리스트

    부작용:
    - 없음(원본 보호)

    오류:
    - 없음
    """

    return [dict(item) for item in items]


def list_lines() -> List[Dict[str, str]]:
    """라인 목록을 반환합니다.

    입력:
    - 없음

    반환:
    - List[Dict[str, str]]: 라인 목록

    부작용:
    - 없음(더미 데이터)

    오류:
    - 없음
    """

    return _clone_items(LINE_LIST)


def list_sdwt_for_line(*, line_id: str) -> List[Dict[str, str]]:
    """라인 기준 SDWT 목록을 반환합니다.

    입력:
    - line_id: 라인 ID

    반환:
    - List[Dict[str, str]]: SDWT 목록

    부작용:
    - 없음(더미 데이터)

    오류:
    - 없음
    """

    line_key = normalize_id(line_id)
    return _clone_items(SDWT_MAP.get(line_key, []))


def list_prc_groups(*, line_id: str, sdwt_id: str) -> List[Dict[str, str]]:
    """라인/SDWT 조합 기준 PRC 그룹 목록을 반환합니다.

    입력:
    - line_id: 라인 ID
    - sdwt_id: SDWT ID(설비/공정 식별자)

    반환:
    - List[Dict[str, str]]: PRC 그룹 목록

    부작용:
    - 없음(더미 데이터)

    오류:
    - 없음
    """

    line_key = normalize_id(line_id)
    sdwt_key = normalize_id(sdwt_id)
    return _clone_items(PRC_GROUPS.get((line_key, sdwt_key), []))


def list_equipments(*, line_id: str, sdwt_id: str, prc_group: str) -> List[Dict[str, str]]:
    """라인/SDWT/PRC 조합 기준 설비 목록을 반환합니다.

    입력:
    - line_id: 라인 ID
    - sdwt_id: SDWT ID(설비/공정 식별자)
    - prc_group: PRC 그룹 코드

    반환:
    - List[Dict[str, str]]: 설비 목록

    부작용:
    - 없음(더미 데이터)

    오류:
    - 없음
    """

    line_key = normalize_id(line_id)
    sdwt_key = normalize_id(sdwt_id)
    prc_key = normalize_id(prc_group)
    return _clone_items(EQUIPMENTS.get((line_key, sdwt_key, prc_key), []))


def get_equipment_info(*, eqp_id: str) -> Dict[str, str] | None:
    """eqpId 기준 설비 메타데이터를 반환합니다.

    입력:
    - eqp_id: 설비 ID

    반환:
    - Dict[str, str] | None: 설비 메타데이터(없으면 None)

    부작용:
    - 없음(더미 데이터)

    오류:
    - 없음
    """

    eqp_key = normalize_id(eqp_id)
    info = EQUIPMENT_INFO.get(eqp_key)
    if not info:
        return None
    return dict(info)


def get_logs_for_equipment(*, eqp_id: str) -> Dict[str, List[Dict[str, object]]]:
    """설비 로그(타입별)를 반환합니다.

    입력:
    - eqp_id: 설비 ID

    반환:
    - Dict[str, List[Dict[str, object]]]: 타입별 로그 묶음

    부작용:
    - 없음(더미 데이터)

    오류:
    - 없음
    """

    eqp_key = normalize_id(eqp_id)
    logs = LOGS.get(eqp_key, {})
    return {key: _clone_items(values) for key, values in logs.items()}


def get_logs_by_type(*, eqp_id: str, log_key: str) -> List[Dict[str, object]]:
    """특정 타입 로그만 반환합니다.

    입력:
    - eqp_id: 설비 ID
    - log_key: 로그 타입 키(eqp, tip 등)

    반환:
    - List[Dict[str, object]]: 타입별 로그 목록

    부작용:
    - 없음(더미 데이터)

    오류:
    - 없음
    """

    eqp_key = normalize_id(eqp_id)
    type_key = (log_key or "").strip().lower()
    return _clone_items(LOGS.get(eqp_key, {}).get(type_key, []))


def get_merged_logs(*, eqp_id: str) -> List[Dict[str, object]]:
    """모든 타입 로그를 합쳐 정렬된 목록으로 반환합니다.

    입력:
    - eqp_id: 설비 ID

    반환:
    - List[Dict[str, object]]: eventTime 기준 정렬된 로그 목록

    부작용:
    - 없음(더미 데이터)

    오류:
    - 없음
    """

    eqp_key = normalize_id(eqp_id)
    eqp_logs = LOGS.get(eqp_key, {})
    merged: List[Dict[str, object]] = []
    for key in ("eqp", "tip", "ctttm", "racb", "jira", "event"):
        merged.extend(_clone_items(eqp_logs.get(key, [])))

    merged.sort(key=lambda log: str(log.get("eventTime") or ""))
    return merged


__all__ = [
    "get_equipment_info",
    "get_logs_by_type",
    "get_merged_logs",
    "list_equipments",
    "list_lines",
    "list_prc_groups",
    "list_sdwt_for_line",
    "normalize_id",
]
