"""data_movement Airflow 트리거 API입니다."""

from __future__ import annotations

import logging
from dataclasses import asdict, is_dataclass
from typing import Any, Callable

from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView

from api.common.services import ensure_airflow_token, parse_json_body_or_error_when_present
from api.data_movement.ct_process_comment.services import load_ct_process_comment_files
from api.data_movement.ctttm_workorder_list.services import load_ctttm_workorder_list_files
from api.data_movement.m_tkin_prevent.services import load_m_tkin_prevent_files

logger = logging.getLogger(__name__)

LoadFunction = Callable[..., Any]


DATA_MOVEMENT_LOADERS: dict[str, LoadFunction] = {
    "m_tkin_prevent": load_m_tkin_prevent_files,
    "ctttm_workorder_list": load_ctttm_workorder_list_files,
    "ct_process_comment": load_ct_process_comment_files,
}


def _parse_optional_positive_int(*, body_value: Any, query_value: Any, field_name: str) -> int | None:
    """body/query 값을 양의 정수 옵션으로 변환합니다."""

    raw_value = query_value if query_value not in (None, "") else body_value
    if raw_value in (None, ""):
        return None
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name}은 1 이상의 정수여야 합니다.") from exc
    if parsed < 1:
        raise ValueError(f"{field_name}은 1 이상의 정수여야 합니다.")
    return parsed


def _parse_optional_bool(*, body_value: Any, query_value: Any, field_name: str) -> bool:
    """body/query 값을 boolean 옵션으로 변환합니다."""

    raw_value = query_value if query_value not in (None, "") else body_value
    if raw_value in (None, ""):
        return False
    if isinstance(raw_value, bool):
        return raw_value
    normalized = str(raw_value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{field_name}은 boolean 값이어야 합니다.")


def _serialize_outcome(outcome: Any) -> dict[str, Any]:
    """loader outcome을 JSON 응답용 dict로 변환합니다."""

    raw = asdict(outcome) if is_dataclass(outcome) else dict(outcome)
    return {key: value for key, value in raw.items() if value is not None}


def _serialize_summary(*, table_name: str, summary: Any) -> dict[str, Any]:
    """loader summary를 JSON 응답용 dict로 변환합니다."""

    outcomes = [_serialize_outcome(outcome) for outcome in summary.outcomes]
    return {
        "table_name": table_name,
        "processed_count": summary.processed_count,
        "success_count": summary.success_count,
        "failure_count": summary.failure_count,
        "outcomes": outcomes,
    }


@method_decorator(csrf_exempt, name="dispatch")
class DataMovementLoadTriggerView(APIView):
    """Airflow에서 data_movement 파일 적재를 트리거합니다."""

    permission_classes: tuple = ()

    def post(self, request: HttpRequest, table_name: str, *args: object, **kwargs: object) -> JsonResponse:
        """테이블별 data_movement loader를 실행합니다."""

        auth_response = ensure_airflow_token(request, require_bearer=True)
        if auth_response is not None:
            return auth_response

        loader = DATA_MOVEMENT_LOADERS.get(table_name)
        if loader is None:
            return JsonResponse({"error": f"지원하지 않는 data_movement 테이블입니다: {table_name}"}, status=404)

        payload, payload_error = parse_json_body_or_error_when_present(request)
        if payload_error is not None:
            return payload_error

        try:
            limit = _parse_optional_positive_int(
                body_value=payload.get("limit"),
                query_value=request.GET.get("limit"),
                field_name="limit",
            )
            dry_run = _parse_optional_bool(
                body_value=payload.get("dry_run"),
                query_value=request.GET.get("dry_run"),
                field_name="dry_run",
            )
            summary = loader(dry_run=dry_run, limit=limit)
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)
        except Exception:
            logger.exception("Failed to trigger data_movement load: %s", table_name)
            return JsonResponse({"error": "data_movement 파일 적재에 실패했습니다."}, status=500)

        response_payload = _serialize_summary(table_name=table_name, summary=summary)
        status_code = 500 if summary.failure_count else 200
        return JsonResponse(response_payload, status=status_code)
