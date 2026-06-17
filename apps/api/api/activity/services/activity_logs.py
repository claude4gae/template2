# =============================================================================
# 모듈 설명: 활동 로그 서비스 로직을 제공합니다.
# - 주요 함수: get_recent_activity_payload, get_app_access_stats_payload, record_app_access
# - 불변 조건: 조회는 셀렉터를 통해 수행하고, 쓰기는 activity 도메인 안에서 처리합니다.
# =============================================================================
from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from ..models import ActivityLog
from ..selectors import (
    APP_ACCESS_ACTION,
    get_recent_activity_logs,
    summarize_app_access_by_app,
    summarize_app_access_by_date,
    summarize_app_access_totals,
)
from ..serializers import serialize_activity_log

KST = ZoneInfo("Asia/Seoul")
DEFAULT_STATS_DAYS = 7
MAX_STATS_DAYS = 90


def _parse_iso_date(value: str | None, *, field_name: str) -> date | None:
    """YYYY-MM-DD 문자열을 date로 변환합니다."""

    if value is None or not value.strip():
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError(f"{field_name} must be YYYY-MM-DD") from exc


def _resolve_stats_range(
    *,
    from_value: str | None,
    to_value: str | None,
    now: datetime | None = None,
) -> tuple[date, date, datetime, datetime]:
    """KST 날짜 범위를 UTC datetime boundary로 변환합니다."""

    current = now or datetime.now(tz=UTC)
    today_kst = current.astimezone(KST).date()
    to_date = _parse_iso_date(to_value, field_name="to") or today_kst
    from_date = _parse_iso_date(from_value, field_name="from") or (to_date - timedelta(days=DEFAULT_STATS_DAYS - 1))

    if from_date > to_date:
        raise ValueError("from must be earlier than or equal to to")

    if (to_date - from_date).days + 1 > MAX_STATS_DAYS:
        raise ValueError(f"date range must be {MAX_STATS_DAYS} days or less")

    start_local = datetime.combine(from_date, time.min, tzinfo=KST)
    end_local = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=KST)
    return from_date, to_date, start_local.astimezone(UTC), end_local.astimezone(UTC)


def _safe_text(value: Any, fallback: str) -> str:
    """집계 row의 문자열 값을 안전하게 반환합니다."""

    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def _serialize_datetime(value: Any) -> str | None:
    """datetime 값을 ISO 문자열로 변환합니다."""

    if isinstance(value, datetime):
        return value.astimezone(KST).isoformat()
    return None


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


def record_app_access(
    *,
    user: Any,
    app_id: str,
    app_name: str,
    path: str,
) -> ActivityLog:
    """앱 화면 진입 이벤트를 ActivityLog에 기록합니다.

    입력:
    - user: 인증 사용자
    - app_id: 앱 식별자
    - app_name: 앱 표시 이름
    - path: 프론트엔드 경로

    반환:
    - ActivityLog: 생성된 앱 접속 이벤트

    부작용:
    - ActivityLog 테이블에 APP_ACCESS 행을 생성합니다.

    오류:
    - DB 저장 실패 시 Django ORM 예외가 발생할 수 있습니다.
    """

    return record_activity_log(
        user=user,
        action=APP_ACCESS_ACTION,
        path=path or f"/app-access/{app_id}",
        method="EVENT",
        status_code=200,
        metadata={
            "event_type": "app_access",
            "app_id": app_id,
            "app_name": app_name,
            "knox_id": getattr(user, "knox_id", "") or "",
        },
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


def get_app_access_stats_payload(
    *,
    from_value: str | None,
    to_value: str | None,
    app_id: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """앱별 접속 통계 payload를 생성합니다.

    입력:
    - from_value/to_value: KST 기준 YYYY-MM-DD 쿼리 문자열
    - app_id: 특정 앱 id 필터(선택)
    - now: 테스트용 현재 시각(선택)

    반환:
    - dict[str, Any]: 대시보드 API 응답 payload

    부작용:
    - 없음(읽기 전용)

    오류:
    - ValueError: 날짜 형식/범위가 유효하지 않을 때
    """

    clean_app_id = app_id.strip() if isinstance(app_id, str) and app_id.strip() else None
    from_date, to_date, start_at, end_at = _resolve_stats_range(
        from_value=from_value,
        to_value=to_value,
        now=now,
    )
    app_rows = summarize_app_access_by_app(start_at=start_at, end_at=end_at, app_id=clean_app_id)
    series_rows = summarize_app_access_by_date(start_at=start_at, end_at=end_at, app_id=clean_app_id)
    totals = summarize_app_access_totals(start_at=start_at, end_at=end_at, app_id=clean_app_id)

    apps: list[dict[str, Any]] = []
    for row in app_rows:
        app_key = _safe_text(row.get("metadata__app_id"), "unknown")
        app_name = _safe_text(row.get("metadata__app_name"), app_key)
        access_count = int(row.get("access_count") or 0)
        unique_user_count = int(row.get("unique_user_count") or 0)
        apps.append(
            {
                "appId": app_key,
                "appName": app_name,
                "accessCount": access_count,
                "uniqueUserCount": unique_user_count,
                "avgAccessPerUser": round(access_count / unique_user_count, 1) if unique_user_count else 0,
                "lastAccessedAt": _serialize_datetime(row.get("last_accessed_at")),
            }
        )

    series = [
        {
            "date": row["local_date"].isoformat() if hasattr(row.get("local_date"), "isoformat") else "",
            "appId": _safe_text(row.get("metadata__app_id"), "unknown"),
            "appName": _safe_text(row.get("metadata__app_name"), _safe_text(row.get("metadata__app_id"), "unknown")),
            "accessCount": int(row.get("access_count") or 0),
        }
        for row in series_rows
    ]

    top_app = apps[0] if apps else None

    return {
        "timezone": "Asia/Seoul",
        "range": {
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
        },
        "summary": {
            "totalAccessCount": totals["access_count"],
            "uniqueUserCount": totals["unique_user_count"],
            "activeAppCount": len(apps),
            "topApp": top_app,
        },
        "apps": apps,
        "series": series,
    }
