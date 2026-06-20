"""racb_list 조회 selector입니다."""

from __future__ import annotations

from datetime import datetime, time
from typing import List
from urllib.parse import urlencode

from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from api.data_movement.racb_list.models import RacbList


def _normalize_datetime_filter(value: object | None, *, is_end: bool = False) -> object | None:
    """문자열 시간 경계를 DateTimeField filter에 안전한 값으로 변환합니다."""

    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = parse_datetime(value)
        if parsed is None:
            parsed_date = parse_date(value)
            if parsed_date is None:
                return value
            parsed = datetime.combine(parsed_date, time.max if is_end else time.min)
    else:
        return value

    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_default_timezone())
    return parsed


def _build_stable_racb_id(row: RacbList) -> str:
    """RACB row의 정렬/필터와 무관한 stable ID를 생성합니다."""

    return f"RACB-{row.c_racb_id}-{row.eqp_cb}"


def _build_event_type(row: RacbList) -> str:
    """기존 RACB 응답과 맞게 RACB 타입과 상태 코드를 조합합니다."""

    return f"{row.racb_type_cd or ''}_{row.status_code or ''}"


def _build_racb_url(row: RacbList) -> str:
    """RACB 상세 팝업 URL을 생성합니다."""

    query = urlencode({"racbId": row.c_racb_id, "lineId": row.line_id or ""})
    return f"{settings.RACB_REPORT_BASE_URL}?{query}"


def fetch_racb_timeline_logs(
    *,
    eqp_id: str,
    start_at: object | None = None,
    end_at: object | None = None,
    limit: int | None = None,
) -> List[dict[str, object]]:
    """timeline RACB 로그 응답 형태로 RACB 이력을 반환합니다.

    입력:
    - eqp_id: 정규화가 끝난 EQP-CB ID
    - start_at/end_at: 조회 시간 경계
    - limit: 선택 row 제한

    반환:
    - List[dict[str, object]]: observer RACB log payload

    부작용:
    - 없음(DB 조회)

    오류:
    - DB 연결 실패 시 예외
    """

    normalized_start_at = _normalize_datetime_filter(start_at)
    normalized_end_at = _normalize_datetime_filter(end_at, is_end=True)

    queryset = RacbList.objects.filter(eqp_cb__iexact=eqp_id).order_by("-update_date")
    if normalized_start_at is not None:
        queryset = queryset.filter(update_date__gte=normalized_start_at)
    if normalized_end_at is not None:
        queryset = queryset.filter(update_date__lte=normalized_end_at)
    if limit is not None:
        queryset = queryset[:limit]

    return [
        {
            "id": _build_stable_racb_id(row),
            "logType": "RACB",
            "eventType": _build_event_type(row),
            "eventTime": row.update_date,
            "operator": row.user_name,
            "comment": row.title,
            "url": _build_racb_url(row),
            "lineId": row.line_id,
            "eqpId": row.eqp_cb,
        }
        for row in queryset
    ]


__all__ = ["fetch_racb_timeline_logs"]
