# =============================================================================
# 모듈: Drone SOP 사용자 소속 매핑 해석
# 주요 기능: sdwt_prod/user_sdwt_prod 조합을 target_user_sdwt_prod로 해석
# 주요 가정: 매핑 규칙은 selectors에서 읽어오며, 매핑이 없으면 실패 처리합니다.
# =============================================================================
"""Drone SOP 대상 소속 해석 유틸리티."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ... import selectors


def _normalize_user_sdwt_value(value: Any) -> str | None:
    """소속 값을 정규화합니다.

    인자:
        value: 원본 값.

    반환:
        정규화된 문자열 또는 None.

    부작용:
        없음. 순수 정규화입니다.
    """

    if value is None:
        return None
    if isinstance(value, str):
        trimmed = value.strip()
        return trimmed if trimmed else None
    trimmed = str(value).strip()
    return trimmed if trimmed else None


def _normalize_user_sdwt_lookup_key(value: Any) -> str | None:
    """대소문자 비구분 비교용 소속 키를 정규화합니다.

    인자:
        value: 원본 값.

    반환:
        공백 제거 후 casefold 적용한 문자열 또는 None.

    부작용:
        없음. 순수 정규화입니다.
    """

    cleaned = _normalize_user_sdwt_value(value)
    if not cleaned:
        return None
    return cleaned.casefold()


@dataclass(frozen=True)
class UserSdwtProdMapIndex:
    """사용자 소속 매핑 인덱스."""

    pair_map: dict[tuple[str, str], list[str]]
    sdwt_only_map: dict[str, list[str]]
    user_only_map: dict[str, list[str]]


def _append_unique_target(*, target_list: list[str], target: str) -> None:
    """target 목록에 대소문자 비구분 중복 없이 값을 추가합니다."""

    target_key = _normalize_user_sdwt_lookup_key(target)
    if not target_key:
        return
    if any(_normalize_user_sdwt_lookup_key(existing) == target_key for existing in target_list):
        return
    target_list.append(target)


def _append_index_target(*, index_map: dict[Any, list[str]], key: Any, target: str) -> None:
    """매핑 인덱스에 target 값을 누적합니다."""

    values = index_map.setdefault(key, [])
    _append_unique_target(target_list=values, target=target)


def _merge_unique_targets(*target_groups: list[str]) -> list[str]:
    """여러 target 목록을 순서 유지 + 중복 제거 방식으로 병합합니다."""

    merged: list[str] = []
    for group in target_groups:
        for target in group:
            _append_unique_target(target_list=merged, target=target)
    return merged


def load_user_sdwt_prod_map_index() -> UserSdwtProdMapIndex:
    """매핑 규칙을 인덱스로 로딩합니다.

    반환:
        UserSdwtProdMapIndex 인스턴스.

    부작용:
        selectors에서 DB 조회가 발생합니다.
    """

    # -----------------------------------------------------------------------------
    # 1) 매핑 규칙 로딩
    # -----------------------------------------------------------------------------
    rows = selectors.list_drone_sop_user_sdwt_maps()
    pair_map: dict[tuple[str, str], list[str]] = {}
    sdwt_only_map: dict[str, list[str]] = {}
    user_only_map: dict[str, list[str]] = {}

    # -----------------------------------------------------------------------------
    # 2) 규칙 정규화 및 인덱싱
    # -----------------------------------------------------------------------------
    for row in rows:
        sdwt = _normalize_user_sdwt_value(row.get("sdwt_prod"))
        user = _normalize_user_sdwt_value(row.get("user_sdwt_prod"))
        target = _normalize_user_sdwt_value(row.get("target_user_sdwt_prod"))
        if not target:
            continue
        sdwt_lookup = _normalize_user_sdwt_lookup_key(sdwt)
        user_lookup = _normalize_user_sdwt_lookup_key(user)
        if sdwt and user:
            assert sdwt_lookup is not None
            assert user_lookup is not None
            _append_index_target(index_map=pair_map, key=(sdwt_lookup, user_lookup), target=target)
        elif sdwt and not user:
            assert sdwt_lookup is not None
            _append_index_target(index_map=sdwt_only_map, key=sdwt_lookup, target=target)
        elif user and not sdwt:
            assert user_lookup is not None
            _append_index_target(index_map=user_only_map, key=user_lookup, target=target)

    return UserSdwtProdMapIndex(
        pair_map=pair_map,
        sdwt_only_map=sdwt_only_map,
        user_only_map=user_only_map,
    )


def resolve_target_user_sdwt_prods(
    *,
    row: dict[str, Any],
    index: UserSdwtProdMapIndex,
) -> list[str]:
    """단일 row에 대한 target_user_sdwt_prod 목록을 해석합니다.

    인자:
        row: Drone SOP 행 dict.
        index: 매핑 인덱스.

    반환:
        우선순위가 가장 높은 매핑 tier의 target_user_sdwt_prod 목록.

    부작용:
        없음. 순수 해석입니다.
    """

    # -----------------------------------------------------------------------------
    # 1) 입력 정규화
    # -----------------------------------------------------------------------------
    persisted_target = _normalize_user_sdwt_value(row.get("target_user_sdwt_prod"))
    sdwt = _normalize_user_sdwt_lookup_key(row.get("sdwt_prod"))
    user = _normalize_user_sdwt_lookup_key(row.get("user_sdwt_prod"))

    # -----------------------------------------------------------------------------
    # 2) 우선순위 매칭
    # -----------------------------------------------------------------------------
    mapped_targets: list[str] = []
    if sdwt and user:
        mapped_targets = _merge_unique_targets(index.pair_map.get((sdwt, user), []))
        if mapped_targets:
            return mapped_targets
    if sdwt:
        mapped_targets = _merge_unique_targets(index.sdwt_only_map.get(sdwt, []))
        if mapped_targets:
            return mapped_targets
    if user:
        mapped_targets = _merge_unique_targets(index.user_only_map.get(user, []))
        if mapped_targets:
            return mapped_targets

    # -----------------------------------------------------------------------------
    # 3) 신규 매핑이 없으면 기존 저장 target을 호환값으로 사용
    # -----------------------------------------------------------------------------
    if persisted_target:
        return [persisted_target]
    return []
