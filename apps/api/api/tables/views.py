# =============================================================================
# 모듈 설명: 테이블 조회/업데이트 APIView를 제공합니다.
# - 주요 클래스: TablesView, TableUpdateView
# - 불변 조건: 비즈니스 로직은 서비스 레이어로 위임합니다.
# =============================================================================

"""테이블 조회 및 업데이트 관련 뷰."""
from __future__ import annotations

import logging

from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView

from api.common.services import DEFAULT_TABLE
from api.common.services import parse_json_body, sanitize_identifier
from api.common.services import (
    merge_activity_metadata,
    set_activity_new_state,
    set_activity_previous_state,
    set_activity_summary,
)

from .services import (
    TableNotFoundError,
    TableRecordNotFoundError,
    get_table_list_payload,
    update_table_record,
)

logger = logging.getLogger(__name__)


class TablesView(APIView):
    """임의 테이블을 조회하여 리스트 형태로 반환."""

    def get(self, request: HttpRequest, *args: object, **kwargs: object) -> JsonResponse:
        """테이블 목록 조회 결과를 반환합니다.

        입력:
        - 요청: Django HttpRequest
        - args/kwargs: URL 라우팅 인자

        반환:
        - JsonResponse: 테이블 조회 payload

        부작용:
        - 없음(읽기 전용)

        오류:
        - 400: 입력 오류(컬럼/날짜 등)
        - 404: 테이블 없음
        - 500: 내부 오류

        예시 요청:
        - 예시 요청: GET /api/v1/tables?table=drone_sop&limit=50

        snake/camel 호환:
        - 해당 없음(쿼리 파라미터만 사용)
        """
        # -----------------------------------------------------------------------------
        # 1) 서비스 호출
        # -----------------------------------------------------------------------------
        try:
            payload = get_table_list_payload(params=request.GET)
            return JsonResponse(payload)
        except TableNotFoundError as exc:
            return JsonResponse({"error": str(exc)}, status=404)
        except (ValueError, LookupError) as exc:
            return JsonResponse({"error": str(exc)}, status=400)
        except Exception:  # 방어적 로깅(커버리지 제외): pragma: no cover
            logger.exception("Failed to load table data")
            return JsonResponse({"error": "Failed to load table data"}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class TableUpdateView(APIView):
    """임의 테이블의 일부분을 PATCH로 갱신."""

    def patch(self, request: HttpRequest, *args: object, **kwargs: object) -> JsonResponse:
        """테이블 레코드를 부분 업데이트합니다.

        입력:
        - 요청: Django HttpRequest
        - args/kwargs: URL 라우팅 인자

        반환:
        - JsonResponse: 성공 여부

        부작용:
        - 테이블 레코드 업데이트
        - 활동 로그 메타데이터 기록

        오류:
        - 400: 입력 오류/JSON 파싱 실패
        - 404: 테이블/레코드 없음
        - 500: 내부 오류

        예시 요청:
        - 예시 요청: PATCH /api/v1/tables/update
          요청 바디 예시: {"table":"drone_sop","id":123,"updates":{"status":"DONE"}}
          요청 바디 예시: {"table":"drone_sop","id":123,"values":{"status":"DONE"}}

        snake/camel 호환:
        - 해당 없음(요청 바디 키는 table/id/updates/values만 사용)
        """
        # -----------------------------------------------------------------------------
        # 1) JSON 바디 파싱
        # -----------------------------------------------------------------------------
        payload = parse_json_body(request)
        if payload is None:
            return JsonResponse({"error": "Invalid JSON body"}, status=400)

        # -----------------------------------------------------------------------------
        # 2) 하위 호환 키 보정(values → updates)
        # -----------------------------------------------------------------------------
        if "updates" not in payload and "values" in payload:
            payload = {**payload, "updates": payload.get("values")}

        # -----------------------------------------------------------------------------
        # 3) 테이블/레코드 식별자 검증
        # -----------------------------------------------------------------------------
        table_name = sanitize_identifier(payload.get("table"), DEFAULT_TABLE)
        if not table_name:
            return JsonResponse({"error": "Invalid table name"}, status=400)

        record_id = payload.get("id")
        if record_id in (None, ""):
            return JsonResponse({"error": "Record id is required"}, status=400)

        # -----------------------------------------------------------------------------
        # 4) 활동 로그 컨텍스트 기록
        # -----------------------------------------------------------------------------
        set_activity_summary(request, f"Update {table_name} record #{record_id}")
        merge_activity_metadata(request, resource=table_name, entryId=record_id)

        # -----------------------------------------------------------------------------
        # 5) 업데이트 수행
        # -----------------------------------------------------------------------------
        try:
            result = update_table_record(payload=payload)
        except TableNotFoundError as exc:
            return JsonResponse({"error": str(exc)}, status=404)
        except TableRecordNotFoundError as exc:
            return JsonResponse({"error": str(exc)}, status=404)
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)
        except Exception:  # 방어적 로깅(커버리지 제외): pragma: no cover
            logger.exception("Failed to update table record")
            return JsonResponse({"error": "Failed to update record"}, status=500)

        # -----------------------------------------------------------------------------
        # 6) 활동 로그 변경 전/후 저장
        # -----------------------------------------------------------------------------
        if result.previous_row is not None:
            set_activity_previous_state(request, result.previous_row)
        if result.updated_row is not None:
            set_activity_new_state(request, result.updated_row)

        # -----------------------------------------------------------------------------
        # 7) 응답 반환
        # -----------------------------------------------------------------------------
        return JsonResponse({"success": True})


__all__ = ["TableUpdateView", "TablesView"]
