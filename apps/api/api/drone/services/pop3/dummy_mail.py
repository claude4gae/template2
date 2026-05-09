# =============================================================================
# 모듈: Drone SOP 더미 메일 API transport
# 주요 기능: 더미 메일 목록 조회 및 삭제
# 주요 가정: 오프라인 개발 환경에서는 POP3 대신 HTTP 더미 메일 API를 사용합니다.
# =============================================================================
"""Drone SOP 더미 메일 API transport 헬퍼 모듈입니다."""

from __future__ import annotations

from typing import Any, Sequence

import requests


def list_dummy_mail_messages(*, url: str, timeout: int) -> list[dict[str, Any]]:
    """더미 메일 API에서 메시지 목록을 조회합니다.

    인자:
        url: 더미 메일 API URL.
        timeout: 요청 타임아웃(초).

    반환:
        메시지 dict 리스트.

    부작용:
        외부 HTTP 요청이 발생합니다.
    """

    # -------------------------------------------------------------------------
    # 1) 메시지 목록 조회
    # -------------------------------------------------------------------------
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    messages = data.get("messages")
    if not isinstance(messages, list):
        return []
    # -------------------------------------------------------------------------
    # 2) dict 필터링 및 정렬
    # -------------------------------------------------------------------------
    normalized: list[dict[str, Any]] = []
    for entry in messages:
        if isinstance(entry, dict):
            normalized.append(entry)
    normalized.sort(key=lambda item: int(item.get("id") or 0))
    return normalized


def delete_dummy_mail_messages(*, url: str, mail_ids: Sequence[int], timeout: int) -> int:
    """더미 메일 API에서 메시지를 삭제합니다.

    인자:
        url: 더미 메일 API URL.
        mail_ids: 삭제할 메시지 ID 목록.
        timeout: 요청 타임아웃(초).

    반환:
        삭제된 메시지 수.

    부작용:
        외부 HTTP 요청이 발생합니다.
    """

    # -------------------------------------------------------------------------
    # 1) 메시지 삭제 요청
    # -------------------------------------------------------------------------
    deleted = 0
    for mail_id in mail_ids:
        resp = requests.delete(f"{url.rstrip('/')}/{mail_id}", timeout=timeout)
        if resp.status_code in {200, 204}:
            deleted += 1
    return deleted


__all__ = ["delete_dummy_mail_messages", "list_dummy_mail_messages"]
