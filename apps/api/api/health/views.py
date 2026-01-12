# =============================================================================
# 모듈 설명: health 체크 APIView를 제공합니다.
# - 주요 클래스: HealthView
# - 불변 조건: 간단한 상태 응답만 반환합니다.
# =============================================================================

"""헬스 체크 관련 뷰."""
from __future__ import annotations

from django.http import HttpRequest, JsonResponse
from rest_framework.views import APIView

from .services import get_health_payload


class HealthView(APIView):
    """단순 헬스 체크 엔드포인트."""

    def get(self, request: HttpRequest, *args: object, **kwargs: object) -> JsonResponse:
        """헬스 체크 응답을 반환합니다.

        입력:
        - 요청: Django HttpRequest
        - args/kwargs: URL 라우팅 인자

        반환:
        - JsonResponse: 상태 정보 JSON

        부작용:
        - 없음

        오류:
        - 없음

        예시 요청:
        - 예시 요청: GET /api/v1/health/

        snake/camel 호환:
        - 해당 없음(요청 바디 없음)
        """
        return JsonResponse(get_health_payload())
