# =============================================================================
# 모듈: L3 Spider API 뷰
# 주요 엔드포인트: meta, summary, data
# 주요 가정: 로그인 사용자만 조회할 수 있습니다.
# =============================================================================
from __future__ import annotations

try:
    import orjson

    def _fast_response(data, status: int = 200):
        from django.http import HttpResponse
        return HttpResponse(
            orjson.dumps(data),
            content_type="application/json; charset=utf-8",
            status=status,
        )
except ImportError:
    from rest_framework.response import Response as _DRFResponse

    def _fast_response(data, status: int = 200):
        return _DRFResponse(data, status=status)

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .serializers import (
    L3SpiderDataRequestSerializer,
    L3SpiderExclusionFilterSerializer,
    L3SpiderFilterCandidatesSerializer,
)


def _error_response(error: Exception) -> Response:
    status_code = getattr(error, "status_code", 400)
    return Response({"error": str(error)}, status=status_code)


class L3SpiderMetaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs) -> Response:
        try:
            return Response(services.get_meta())
        except services.L3SpiderServiceError as error:
            return _error_response(error)


class L3SpiderStructureView(APIView):
    """파일명 스캔만으로 edsStepSeqs·edsStepPpids를 즉시 반환합니다."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs) -> Response:
        serializer = L3SpiderDataRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            return Response(services.get_structure(serializer.validated_data))
        except services.L3SpiderServiceError as error:
            return _error_response(error)


class L3SpiderStatsView(APIView):
    """slim parquet 읽기로 stats + PPID별 last_tkin_time을 반환합니다."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs) -> Response:
        serializer = L3SpiderDataRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            return _fast_response(services.get_stats(serializer.validated_data))
        except services.L3SpiderServiceError as error:
            return _error_response(error)


class L3SpiderSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs) -> Response:
        serializer = L3SpiderDataRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            return Response(services.get_summary(serializer.validated_data))
        except services.L3SpiderServiceError as error:
            return _error_response(error)


class L3SpiderDataView(APIView):
    """차트 행 데이터: orjson + 컬럼 포맷으로 빠르게 반환합니다."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = L3SpiderDataRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            return _fast_response(services.get_data(serializer.validated_data))
        except services.L3SpiderServiceError as error:
            return _error_response(error)


class L3SpiderExclusionFilterListCreateView(APIView):
    """제외 필터 목록 조회 및 생성."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs) -> Response:
        from .models import L3SpiderExclusionFilter
        filters = L3SpiderExclusionFilter.objects.select_related("created_by").all()
        data = [
            {
                "id": f.id,
                "lineId": f.line_id,
                "processId": f.process_id,
                "edsStep": f.eds_step,
                "stepSeq": f.step_seq,
                "ppid": f.ppid,
                "eqpch": f.eqpch,
                "binName": f.bin_name,
                "dateFrom": f.date_from.isoformat() if f.date_from else None,
                "dateTo": f.date_to.isoformat() if f.date_to else None,
                "isActive": f.is_active,
                "memo": f.memo,
                "createdBy": f.created_by.get_full_name() or f.created_by.username
                if f.created_by else None,
                "createdAt": f.created_at.strftime("%Y-%m-%d %H:%M"),
                "updatedAt": f.updated_at.strftime("%Y-%m-%d %H:%M"),
            }
            for f in filters
        ]
        return Response(data)

    def post(self, request, *args, **kwargs) -> Response:
        serializer = L3SpiderExclusionFilterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        from .models import L3SpiderExclusionFilter
        f = L3SpiderExclusionFilter.objects.create(
            line_id=d["line_id"],
            process_id=d["process_id"],
            eds_step=d["eds_step"],
            step_seq=d["step_seq"],
            ppid=d["ppid"],
            eqpch=d["eqpch"],
            bin_name=d["bin_name"],
            date_from=d.get("date_from"),
            date_to=d.get("date_to"),
            is_active=d["is_active"],
            memo=d.get("memo", ""),
            created_by=request.user if request.user.is_authenticated else None,
        )
        services.invalidate_exclusion_cache()
        return Response({"id": f.id}, status=201)


class L3SpiderExclusionFilterDetailView(APIView):
    """제외 필터 단건 수정/삭제."""

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk: int, *args, **kwargs) -> Response:
        from .models import L3SpiderExclusionFilter
        try:
            f = L3SpiderExclusionFilter.objects.get(pk=pk)
        except L3SpiderExclusionFilter.DoesNotExist:
            return Response({"error": "Not found"}, status=404)
        serializer = L3SpiderExclusionFilterSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        field_map = {
            "line_id": "line_id", "process_id": "process_id", "eds_step": "eds_step",
            "step_seq": "step_seq", "ppid": "ppid", "eqpch": "eqpch",
            "bin_name": "bin_name", "date_from": "date_from", "date_to": "date_to",
            "is_active": "is_active", "memo": "memo",
        }
        for src, dst in field_map.items():
            if src in d:
                setattr(f, dst, d[src])
        f.save()
        services.invalidate_exclusion_cache()
        return Response({"id": f.id})

    def delete(self, request, pk: int, *args, **kwargs) -> Response:
        from .models import L3SpiderExclusionFilter
        try:
            f = L3SpiderExclusionFilter.objects.get(pk=pk)
        except L3SpiderExclusionFilter.DoesNotExist:
            return Response({"error": "Not found"}, status=404)
        f.delete()
        services.invalidate_exclusion_cache()
        return Response(status=204)


class L3SpiderFilterCandidatesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs) -> Response:
        serializer = L3SpiderFilterCandidatesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            return Response(services.get_filter_candidates(serializer.validated_data))
        except services.L3SpiderServiceError as error:
            return _error_response(error)
