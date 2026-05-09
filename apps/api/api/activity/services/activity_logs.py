# =============================================================================
# 모듈 설명: 활동 로그 서비스 로직을 제공합니다.
# - 주요 함수: get_recent_activity_payload, record_activity_log
# - 불변 조건: 조회는 셀렉터를 통해 수행하고, 쓰기는 activity 도메인 안에서 처리합니다.
# =============================================================================
from __future__ import annotations

from typing import Any

from ..models import ActivityLog
from ..selectors import get_recent_activity_logs
from ..serializers import serialize_activity_log


def record_activity_log(
    *,
    user: Any | None,
    action: str,
    path: str,
    method: str,
    status_code: int,
    metadata: dict[str, Any],
) -> ActivityLog:
    """ActivityLog 행을 생성합니다.

    입력:
    - user: 인증 사용자 또는 None
    - action: 요청을 설명하는 액션 이름
    - path: 요청 경로
    - method: HTTP 메서드
    - status_code: 응답 상태 코드
    - metadata: 요청/응답 부가 정보

    반환:
    - ActivityLog: 생성된 활동 로그 인스턴스

    부작용:
    - ActivityLog 테이블에 행을 생성합니다.

    오류:
    - DB 저장 실패 시 Django ORM 예외가 발생할 수 있습니다.
    """

    return ActivityLog.objects.create(
        user=user,
        action=action,
        path=path,
        method=method,
        status_code=status_code,
        metadata=metadata,
    )


def get_recent_activity_payload(*, limit: int) -> list[dict[str, Any]]:
    """최근 ActivityLog 목록을 직렬화해 반환합니다.

    입력:
    - limit: 최대 반환 개수

    반환:
    - list[dict[str, Any]]: 직렬화된 activity log 리스트

    부작용:
    - 없음(읽기 전용)

    오류:
    - 없음
    """

    logs = get_recent_activity_logs(limit=limit)
    return [serialize_activity_log(entry) for entry in logs]
