# =============================================================================
# 모듈: Drone SOP POP3 row builder
# 주요 기능: 메일 HTML data 태그를 DroneSOP upsert row로 변환
# 주요 가정: 수집 orchestration은 이 모듈의 순수 row 생성 결과만 사용합니다.
# =============================================================================
"""Drone SOP POP3 row 생성 헬퍼 모듈입니다."""

from __future__ import annotations

from typing import Any, Optional

from bs4 import BeautifulSoup

from ... import selectors
from ...models import build_sop_key
from ..shared.notify_resolver import (
    UserSdwtProdMapIndex,
    load_user_sdwt_prod_map_index,
    resolve_target_user_sdwt_prods,
)
from .config import NeedToSendRule
from .defect_json import serialize_defect_json_entries
from .utils import sanitize_url


def _normalize_blank(value: Any) -> Any:
    """빈 문자열을 None으로 정규화합니다.

    인자:
        value: 원본 값.

    반환:
        None 또는 원본/변환 값.

    부작용:
        없음. 순수 정규화입니다.
    """

    # -------------------------------------------------------------------------
    # 1) None/빈 문자열 처리
    # -------------------------------------------------------------------------
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return value


def _normalize_user_sdwt_lookup_key(value: Any) -> str | None:
    """대소문자 비구분 비교용 user_sdwt_prod 키를 정규화합니다."""

    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    return cleaned.casefold()


def _extract_first_data_tag(html: str) -> dict[str, str]:
    """HTML에서 첫 번째 <data> 태그의 자식 정보를 추출합니다.

    인자:
        html: HTML 문자열.

    반환:
        태그명 → 텍스트 값을 담은 dict.

    부작용:
        없음. 파싱만 수행합니다.
    """

    # -------------------------------------------------------------------------
    # 1) HTML 파싱 및 data 태그 탐색
    # -------------------------------------------------------------------------
    soup = BeautifulSoup(html, "html.parser")
    data = soup.find("data")
    if not data:
        return {}
    # -------------------------------------------------------------------------
    # 2) 직계 자식 태그 텍스트 추출
    # -------------------------------------------------------------------------
    parsed: dict[str, str] = {}
    for child in data.find_all(recursive=False):
        if not child.name:
            continue
        name = str(child.name).lower()
        if name == "defect_json":
            parsed[name] = child.decode_contents().strip()
            continue
        parsed[name] = child.get_text(strip=True)
    return parsed


def _strip_prefix_num(value: Optional[str]) -> Optional[int]:
    """접두사 2자를 제외한 숫자 부분을 정수로 변환합니다.

    인자:
        value: 접두사가 포함된 문자열.

    반환:
        숫자 부분 정수 또는 None.

    부작용:
        없음. 순수 파싱입니다.
    """

    # -------------------------------------------------------------------------
    # 1) 길이/형식 검증
    # -------------------------------------------------------------------------
    if not value or len(value) <= 2:
        return None
    numeric = value[2:]
    return int(numeric) if numeric.isdigit() else None


def _get_needtosend_rule_for_target(
    *,
    target_user_sdwt_prod: str,
    cache: dict[str, NeedToSendRule | None],
) -> NeedToSendRule | None:
    """target_user_sdwt_prod 기준 needtosend 룰을 조회/캐시합니다.

    인자:
        target_user_sdwt_prod: 해석된 대상 소속 값.
        cache: 규칙 캐시(dict).

    반환:
        NeedToSendRule 또는 None.

    부작용:
        첫 조회 시 DB 읽기가 발생할 수 있습니다.
    """

    # -------------------------------------------------------------------------
    # 1) 캐시 키 정규화 및 조회
    # -------------------------------------------------------------------------
    lookup_key = _normalize_user_sdwt_lookup_key(target_user_sdwt_prod)
    if not lookup_key:
        return None

    cached = cache.get(lookup_key)
    if cached is not None or lookup_key in cache:
        return cached

    # -------------------------------------------------------------------------
    # 2) DB 규칙 조회 후 캐시 적재
    # -------------------------------------------------------------------------
    rule_model = selectors.get_drone_sop_needtosend_rule_by_target(
        target_user_sdwt_prod=target_user_sdwt_prod,
    )
    if not rule_model:
        cache[lookup_key] = None
        return None

    rule = NeedToSendRule(
        comment_last_at=str(rule_model.needtosend_comment_last_at or "").strip(),
        ignore_sample_type=bool(rule_model.needtosend_ignore_sample_type),
    )
    cache[lookup_key] = rule
    return rule


def _compute_needtosend_by_target(
    *,
    row: dict[str, Any],
    target_user_sdwt_prod: str | None,
    rule_cache: dict[str, NeedToSendRule | None],
) -> int:
    """target_user_sdwt_prod 기준으로 needtosend 값을 계산합니다.

    인자:
        row: Drone SOP 행 dict(행 데이터).
        target_user_sdwt_prod: 매핑된 대상 소속(없으면 None).
        rule_cache: 규칙 캐시(dict).

    반환:
        needtosend 값(0/1).

    부작용:
        없음. 순수 계산입니다.
    """

    # -------------------------------------------------------------------------
    # 1) 매핑 없음 → 발송 차단
    # -------------------------------------------------------------------------
    if not isinstance(target_user_sdwt_prod, str):
        return 0
    normalized = target_user_sdwt_prod.strip()
    if not normalized:
        return 0

    # -------------------------------------------------------------------------
    # 2) 활성 DB 규칙 적용 (없으면 발송 차단)
    # -------------------------------------------------------------------------
    rule = _get_needtosend_rule_for_target(target_user_sdwt_prod=normalized, cache=rule_cache)
    if rule:
        return rule.compute(row)
    return 0


def build_drone_sop_row(
    *,
    html: str,
    early_inform_map: dict[tuple[str, str], Optional[str]],
    user_sdwt_map_index: UserSdwtProdMapIndex | None = None,
    needtosend_rule_cache: dict[str, NeedToSendRule | None] | None = None,
) -> Optional[dict[str, Any]]:
    """메일 HTML에서 Drone SOP row를 생성합니다.

    인자:
        html: 메일 HTML 본문.
        early_inform_map: (user_sdwt_prod, main_step) → custom_end_step 매핑.
        user_sdwt_map_index: target_user_sdwt_prod 매핑 인덱스(옵션).
        needtosend_rule_cache: target_user_sdwt_prod 규칙 캐시(옵션).

    반환:
        Drone SOP row dict 또는 None.

    부작용:
        없음. 순수 파싱입니다.
    """

    # -------------------------------------------------------------------------
    # 1) <data> 태그 파싱
    # -------------------------------------------------------------------------
    data = _extract_first_data_tag(html)
    if not data:
        return None

    # -------------------------------------------------------------------------
    # 2) 필드 정규화 및 row 구성
    # -------------------------------------------------------------------------
    normalized = {key: _normalize_blank(value) for key, value in data.items()}
    raw_knox_value = normalized.get("knox_id") or normalized.get("knoxid")
    if isinstance(raw_knox_value, str):
        trimmed_knox = raw_knox_value.strip()
        knox_value = trimmed_knox if trimmed_knox else None
    else:
        knox_value = None
    user_sdwt_prod = normalized.get("user_sdwt_prod")

    # -------------------------------------------------------------------------
    # 2-1) knox_id/user_sdwt_prod가 모두 없으면 기본값을 채웁니다.
    # -------------------------------------------------------------------------
    if not knox_value and not user_sdwt_prod:
        knox_value = "System"
        user_sdwt_prod = "System"

    defect_png_url_source = sanitize_url(normalized.get("defect_png_url"))
    defect_url = serialize_defect_json_entries(
        defect_json=normalized.get("defect_json"),
        defect_png_url=defect_png_url_source,
    )

    row: dict[str, Any] = {
        "line_id": normalized.get("line_id"),
        "sdwt_prod": normalized.get("sdwt_prod"),
        "sample_type": normalized.get("sample_type"),
        "sample_group": normalized.get("sample_group"),
        "eqp_id": normalized.get("eqp_id"),
        "chamber_ids": (str(normalized.get("chamber_ids") or "").replace(",", "")) or None,
        "lot_id": normalized.get("lot_id"),
        "proc_id": normalized.get("proc_id"),
        "ppid": normalized.get("ppid"),
        "main_step": normalized.get("main_step"),
        "metro_current_step": normalized.get("metro_current_step"),
        "metro_steps": normalized.get("metro_steps"),
        "metro_end_step": normalized.get("metro_end_step"),
        "status": normalized.get("status"),
        "knox_id": knox_value,
        "user_sdwt_prod": user_sdwt_prod,
        "comment": normalized.get("comment"),
        "defect_url": defect_url,
        "instant_inform": 0,
    }
    # -------------------------------------------------------------------------
    # 3) sop_key 생성
    # -------------------------------------------------------------------------
    row["sop_key"] = build_sop_key(
        line_id=row.get("line_id"),
        eqp_id=row.get("eqp_id"),
        chamber_ids=row.get("chamber_ids"),
        lot_id=row.get("lot_id"),
        main_step=row.get("main_step"),
    )

    # -------------------------------------------------------------------------
    # 4) 조기 알림 기준 custom_end_step 적용
    # -------------------------------------------------------------------------
    user_sdwt_prod = _normalize_user_sdwt_lookup_key(row.get("user_sdwt_prod")) or ""
    main_step = str(row.get("main_step") or "").strip()
    custom_end_step = early_inform_map.get((user_sdwt_prod, main_step))
    if custom_end_step is not None:
        row["custom_end_step"] = custom_end_step
        current_num = _strip_prefix_num(str(row.get("metro_current_step") or "").strip() or None)
        end_num = _strip_prefix_num(str(custom_end_step).strip() or None)
        if current_num is not None and end_num is not None and current_num >= end_num:
            row["status"] = "COMPLETE"

    # -------------------------------------------------------------------------
    # 5) needtosend 계산
    # -------------------------------------------------------------------------
    if user_sdwt_map_index is None:
        user_sdwt_map_index = load_user_sdwt_prod_map_index()
    if needtosend_rule_cache is None:
        needtosend_rule_cache = {}

    target_user_sdwt_prods = resolve_target_user_sdwt_prods(row=row, index=user_sdwt_map_index)
    target_user_sdwt_prod = target_user_sdwt_prods[0] if target_user_sdwt_prods else None
    row["target_user_sdwt_prods"] = target_user_sdwt_prods
    row["target_user_sdwt_prod"] = target_user_sdwt_prod
    row["needtosend"] = int(
        any(
            _compute_needtosend_by_target(
                row=row,
                target_user_sdwt_prod=target,
                rule_cache=needtosend_rule_cache,
            )
            == 1
            for target in target_user_sdwt_prods
        )
    )
    return row


__all__ = ["build_drone_sop_row"]
