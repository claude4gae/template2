"""mi_tip_update_hist 조회 selector입니다."""

from __future__ import annotations

import hashlib
from datetime import datetime, time
from typing import List

from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from api.data_movement.mi_tip_update_hist.models import MiTipUpdateHist


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


def _format_tip_timestamp(value: object) -> str:
    """timeline ID에 사용할 timestamp 문자열을 생성합니다."""

    if hasattr(value, "strftime"):
        return value.strftime("%Y%m%d%H%M%S%f")
    return str(value or "").replace("-", "").replace(":", "").replace(" ", "")


def _format_tip_comment_hash(value: object) -> str:
    """기존 TIP stable ID와 호환되는 comment md5 값을 생성합니다."""

    return hashlib.md5(str(value or "").encode("utf-8")).hexdigest()


def _format_tip_log_id(row: MiTipUpdateHist) -> str:
    """observer timeline에서 사용할 TIP log ID를 생성합니다."""

    return "-".join(
        [
            "TIP",
            row.eqp_cb,
            _format_tip_timestamp(row.gpm_update_date),
            row.event_type or "",
            row.process_id or "",
            row.step_seq or "",
            row.ppid or "",
            _format_tip_comment_hash(row.tip_comment),
        ]
    )


def fetch_tip_timeline_logs(
    *,
    eqp_id: str,
    start_at: object | None = None,
    end_at: object | None = None,
    limit: int | None = None,
) -> List[dict[str, object]]:
    """timeline TIP 로그 응답 형태로 TIP 이력을 반환합니다.

    입력:
    - eqp_id: 정규화가 끝난 EQP-CB ID
    - start_at/end_at: 조회 시간 경계
    - limit: 선택 row 제한

    반환:
    - List[dict[str, object]]: observer TIP log payload

    부작용:
    - 없음(DB 조회)

    오류:
    - DB 연결 실패 시 예외
    """

    normalized_start_at = _normalize_datetime_filter(start_at)
    normalized_end_at = _normalize_datetime_filter(end_at, is_end=True)

    queryset = MiTipUpdateHist.objects.filter(eqp_cb__iexact=eqp_id).order_by("-gpm_update_date")
    if normalized_start_at is not None:
        queryset = queryset.filter(gpm_update_date__gte=normalized_start_at)
    if normalized_end_at is not None:
        queryset = queryset.filter(gpm_update_date__lte=normalized_end_at)
    if limit is not None:
        queryset = queryset[:limit]

    return [
        {
            "id": _format_tip_log_id(row),
            "eqpId": row.eqp_cb,
            "logType": "TIP",
            "eventType": row.event_type,
            "eventTime": row.gpm_update_date,
            "operator": (row.register_name or "").split("-", 1)[0] or None,
            "comment": row.tip_comment,
            "lineId": row.line_id,
            "process": row.process_id,
            "step": row.step_seq,
            "ppid": row.ppid,
        }
        for row in queryset
    ]


__all__ = ["fetch_tip_timeline_logs"]
