# =============================================================================
# 모듈: Drone SOP defectmap 임시 사이드카
# 주요 기능: defect_url JSON 기반 defectmap API POST 전송
# 주요 가정: 본 기능은 부가 기능이며 실패해도 메인 ingest 흐름은 계속됩니다.
# =============================================================================
"""Drone SOP defectmap 임시 연동 사이드카 모듈입니다."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

import requests

from django.utils import timezone

from .config import DroneSopPop3Config

logger = logging.getLogger(__name__)
_KST_TZ = timezone.get_fixed_timezone(540)
_DEFECT_IMAGE_BASE_URL = "https://app.nyms.samsungds.net"
_DEFECT_IMAGE_PATH = "/map/api/map-image/v3/defect-map"
_DEFECT_IMAGE_STATIC_QUERY = (
    ("profileid", "DEFAULT"),
    ("themeid", "DEFAULT"),
    ("width", "500"),
    ("height", "500"),
    ("site", "GH"),
    ("targetDB", "APP"),
    ("useCache", "true"),
    ("includeCoordinate", "false"),
)


def _extract_defect_entries(value: Any) -> list[dict[str, Any]]:
    """defect_url JSON 문자열에서 dict entry 목록을 추출합니다."""

    if isinstance(value, list):
        return [entry for entry in value if isinstance(entry, dict)]
    raw = str(value or "").strip()
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if isinstance(parsed, list):
        return [entry for entry in parsed if isinstance(entry, dict)]
    if isinstance(parsed, dict):
        return [parsed]
    return []


def _normalize_image_rows(value: Any) -> list[int]:
    """defect_url JSON의 image_rows 값을 selected_row 정수 목록으로 정규화합니다."""

    if not isinstance(value, list):
        return []
    rows: list[int] = []
    for item in value:
        try:
            selected_row = int(item)
        except (TypeError, ValueError):
            continue
        if selected_row >= 0:
            rows.append(selected_row)
    return rows


def _build_defect_image_url(*, map_file: str, selected_row: int) -> str | None:
    """고정 base URL과 file/selected_row로 defect image URL을 생성합니다."""

    if not map_file:
        return None
    query = [
        ("file", map_file),
        ("selected_row", str(selected_row)),
        *_DEFECT_IMAGE_STATIC_QUERY,
    ]
    return f"{_DEFECT_IMAGE_BASE_URL}{_DEFECT_IMAGE_PATH}?{urlencode(query)}"


def _build_defectmap_data_from_defect_url(value: Any) -> str | None:
    """defect_url JSON에서 defectmap API의 기존 data 문자열을 재구성합니다."""

    image_urls: list[str] = []
    for entry in _extract_defect_entries(value):
        map_file = str(entry.get("map_file") or "").strip()
        if not map_file:
            continue
        for selected_row in _normalize_image_rows(entry.get("image_rows")):
            image_url = _build_defect_image_url(
                map_file=map_file,
                selected_row=selected_row,
            )
            if image_url:
                image_urls.append(image_url)
    if not image_urls:
        return None
    return ",".join(image_urls)


def _format_scandate_at_kst(*, scanned_at: datetime) -> str:
    """파싱 시점을 KST 기준 `YYYY-MM-DD HH:MM:SS.mmm +0900`로 포맷합니다.

    인자:
        scanned_at: 파싱 시점 datetime.

    반환:
        KST 기준 scandate 문자열.

    부작용:
        없음. 순수 포맷팅입니다.
    """

    normalized = scanned_at
    if timezone.is_naive(normalized):
        normalized = timezone.make_aware(normalized, _KST_TZ)
    localized = timezone.localtime(normalized, _KST_TZ)
    milliseconds = localized.microsecond // 1000
    return f"{localized:%Y-%m-%d %H:%M:%S}.{milliseconds:03d} {localized:%z}"


def post_defect_png_sidecar_if_needed(
    *,
    row: dict[str, Any],
    config: DroneSopPop3Config,
    scanned_at: datetime,
    error_label: str,
) -> None:
    """임시 부가기능으로 defectmap POST를 수행합니다.

    인자:
        row: 파싱된 Drone SOP row dict.
        config: POP3 수집 설정.
        scanned_at: 파싱 시점 시각.
        error_label: 로그 식별용 라벨.

    반환:
        없음.

    부작용:
        조건 충족 시 외부 HTTP POST 요청이 발생합니다.
        요청 실패는 로그만 남기고 예외를 전파하지 않습니다.
    """

    # -------------------------------------------------------------------------
    # 1) 실행 조건 점검
    # -------------------------------------------------------------------------
    endpoint = str(config.defectmap_url or "").strip()
    if not endpoint:
        return

    defectmap_data = _build_defectmap_data_from_defect_url(row.get("defect_url"))
    if not defectmap_data:
        return

    # -------------------------------------------------------------------------
    # 2) payload 구성
    # -------------------------------------------------------------------------
    payload = {
        "lotid": str(row.get("lot_id") or "").strip(),
        "scandate": _format_scandate_at_kst(scanned_at=scanned_at),
        "step": str(row.get("main_step") or "").strip(),
        "stepid": str(row.get("metro_current_step") or "").strip(),
        "data": defectmap_data,
    }

    # -------------------------------------------------------------------------
    # 3) POST 전송 (실패 시 메인 흐름에 영향 없음)
    # -------------------------------------------------------------------------
    try:
        response = requests.post(endpoint, json=payload, timeout=config.timeout)
        response.raise_for_status()
    except Exception:
        logger.exception("Failed to post defectmap payload for %s", error_label)


__all__ = ["post_defect_png_sidecar_if_needed"]
