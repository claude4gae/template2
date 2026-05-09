# =============================================================================
# 모듈 설명: 활동 로그 조회 APIView를 제공합니다.
# - 주요 클래스: ActivityLogView
# - 불변 조건: 권한 확인 후 최근 로그만 반환합니다.
# =============================================================================

"""액티비티 로그 조회 엔드포인트를 제공합니다."""
from __future__ import annotations

from typing import Any

from django.http import HttpRequest, JsonResponse
from rest_framework.views import APIView

from .services import get_recent_activity_payload

# 조회 건수 관련 상수(한 곳에서 관리)
DEFAULT_LIMIT: int = 50
MAX_LIMIT: int = 200
MIN_LIMIT: int = 1
VIEW_ACTIVITY_LOG_PERMISSIONS = ("activity.view_activitylog", "api.view_activitylog")


def _parse_activity_log_limit(raw_limit: str | None) -> int:
    """limit 쿼리 값을 기존 규칙대로 기본값/허용 범위 안으로 정규화합니다."""

    try:
        limit = int(raw_limit) if raw_limit is not None else DEFAULT_LIMIT
    except (TypeError, ValueError):
        # 비정상 값은 기존 API 동작처럼 오류 대신 기본값으로 처리합니다.
        limit = DEFAULT_LIMIT

    return max(MIN_LIMIT, min(limit, MAX_LIMIT))


def _can_view_activity_logs(user: Any) -> bool:
    """현재 사용자가 ActivityLog 조회 권한을 하나라도 보유했는지 확인합니다."""

    return any(user.has_perm(permission) for permission in VIEW_ACTIVITY_LOG_PERMISSIONS)


class ActivityLogView(APIView):
    """최근 액티비티 로그 조회.

    - 인증 필요
    - 권한 코드: "activity.view_activitylog" 또는 "api.view_activitylog"
    - GET 파라미터:
        - limit (int, optional): 반환 개수. 기본 50, 최소 1, 최대 200.
    """

    def get(self, request: HttpRequest, *args: object, **kwargs: object) -> JsonResponse:
        """최근 로그를 최대 limit개까지 반환합니다.

        입력:
        - 요청: Django HttpRequest
        - args/kwargs: URL 라우팅 인자

        반환:
        - JsonResponse: {"results": [...]} 형태의 응답

        부작용:
        - 없음(읽기 전용)

        오류:
        - 401: 인증 실패
        - 403: 권한 없음

        예시 요청:
        - 예시 요청: GET /api/v1/activity/logs?limit=50

        응답 필드:
        - 필드: id, user, role, action, path, method, status, metadata, timestamp

        snake/camel 호환:
        - 해당 없음(쿼리 파라미터 limit만 사용)
        """
        # -----------------------------------------------------------------------------
        # 1) 인증/권한 체크
        # -----------------------------------------------------------------------------
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Unauthorized"}, status=401)

        if not _can_view_activity_logs(request.user):
            return JsonResponse({"error": "Forbidden"}, status=403)

        # -----------------------------------------------------------------------------
        # 2) limit 파라미터 파싱/정규화
        # -----------------------------------------------------------------------------
        limit = _parse_activity_log_limit(request.GET.get("limit"))

        # -----------------------------------------------------------------------------
        # 3) payload 생성
        # -----------------------------------------------------------------------------
        payload = get_recent_activity_payload(limit=limit)

        # -----------------------------------------------------------------------------
        # 4) 응답 반환
        # -----------------------------------------------------------------------------
        return JsonResponse({"results": payload})


__all__ = ["ActivityLogView"]
