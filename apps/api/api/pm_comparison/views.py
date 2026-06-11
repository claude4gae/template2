# =============================================================================
# 모듈: PM SPIDER API 뷰
# 주요 엔드포인트: meta, compare
# 주요 가정: 로그인 사용자만 파일 기반 분석 결과를 조회할 수 있습니다.
# =============================================================================
from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .serializers import PmComparisonRequestSerializer


def _error_response(error: Exception) -> Response:
    """서비스 오류를 일관된 JSON 응답으로 변환합니다."""

    status_code = getattr(error, "status_code", 400)
    return Response({"error": str(error)}, status=status_code)


class PmComparisonMetaView(APIView):
    """PM SPIDER 데이터 선택 메타데이터를 반환합니다."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs) -> Response:
        """사용 가능한 partition 값 목록을 반환합니다."""

        try:
            return Response(services.get_meta())
        except services.PmComparisonServiceError as error:
            return _error_response(error)


class PmComparisonCompareView(APIView):
    """PM SPIDER 기준 전후 비교 결과를 반환합니다."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs) -> Response:
        """선택 조건과 PM 시점 기준 trace/OES delta를 반환합니다."""

        serializer = PmComparisonRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            return Response(services.compare_pm_window(serializer.validated_data))
        except services.PmComparisonServiceError as error:
            return _error_response(error)
