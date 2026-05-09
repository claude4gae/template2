"""Drone SOP Jira 이슈 생성 API transport helper."""

from __future__ import annotations

import logging
from typing import Any, Sequence

import requests

from .config import DroneJiraConfig
from .issue_fields import build_jira_issue_fields

logger = logging.getLogger(__name__)

ValidJiraIssuePayload = tuple[int, dict[str, Any], dict[str, Any]]


def safe_json(response: requests.Response) -> dict[str, Any]:
    """응답을 안전하게 JSON dict로 변환합니다.

    인자:
        response: requests.Response 객체.

    반환:
        dict 형태의 JSON(실패 시 빈 dict).

    부작용:
        없음. 순수 파싱입니다.
    """

    try:
        parsed = response.json()
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def collect_valid_jira_issue_payloads(
    *,
    rows: Sequence[dict[str, Any]],
    config: DroneJiraConfig,
    project_key_by_id: dict[int, str],
    template_key_by_id: dict[int, str],
) -> list[ValidJiraIssuePayload]:
    """Jira 전송 가능한 row와 payload를 함께 수집합니다."""

    payloads: list[ValidJiraIssuePayload] = []
    for row in rows:
        rid = row.get("delivery_id")
        if not isinstance(rid, int):
            rid = row.get("id")
        if not isinstance(rid, int):
            continue

        project_key = project_key_by_id.get(rid)
        if not project_key:
            continue

        template_key = template_key_by_id.get(rid)
        if not template_key:
            continue

        payloads.append(
            (
                rid,
                row,
                {
                    "fields": build_jira_issue_fields(
                        row=row,
                        project_key=project_key,
                        template_key=template_key,
                        config=config,
                    )
                },
            )
        )
    return payloads


def bulk_create_jira_issues(
    *,
    rows: Sequence[dict[str, Any]],
    config: DroneJiraConfig,
    session: requests.Session,
    project_key_by_id: dict[int, str],
    template_key_by_id: dict[int, str],
) -> tuple[list[int], dict[int, str]]:
    """Jira 벌크 생성 API로 이슈를 생성합니다.

    인자:
        rows: Drone SOP row 목록.
        config: Jira 설정.
        session: Jira 세션.
        project_key_by_id: sop_id → project_key 매핑.
        template_key_by_id: sop_id → template_key 매핑.
    """

    done_ids: list[int] = []
    key_by_id: dict[int, str] = {}

    for st in range(0, len(rows), config.bulk_size):
        chunk = list(rows[st : st + config.bulk_size])
        valid_payloads = collect_valid_jira_issue_payloads(
            rows=chunk,
            config=config,
            project_key_by_id=project_key_by_id,
            template_key_by_id=template_key_by_id,
        )
        if not valid_payloads:
            continue

        try:
            resp = session.post(
                config.bulk_url,
                json={"issueUpdates": [payload for _, _, payload in valid_payloads]},
                timeout=(config.connect_timeout, config.read_timeout),
            )
        except requests.RequestException:
            logger.exception(
                "Jira bulk create request failed(start=%s, size=%s)",
                st,
                len(valid_payloads),
            )
            continue
        if resp.status_code != 201:
            logger.error("Jira bulk create failed %s: %s", resp.status_code, resp.text[:300])
            continue

        data = safe_json(resp)
        issues = data.get("issues") or []
        if not isinstance(issues, list):
            continue

        for index, (rid, _, _) in enumerate(valid_payloads):
            if index >= len(issues):
                continue
            issue = issues[index]
            if not isinstance(issue, dict):
                continue
            key = issue.get("key")
            if isinstance(key, str) and key.strip():
                key_by_id[rid] = key.strip()
                done_ids.append(rid)

    return done_ids, key_by_id


def single_create_jira_issues(
    *,
    rows: Sequence[dict[str, Any]],
    config: DroneJiraConfig,
    session: requests.Session,
    project_key_by_id: dict[int, str],
    template_key_by_id: dict[int, str],
) -> tuple[list[int], dict[int, str]]:
    """Jira 단건 생성 API로 이슈를 생성합니다.

    인자:
        rows: Drone SOP row 목록.
        config: Jira 설정.
        session: Jira 세션.
        project_key_by_id: sop_id → project_key 매핑.
        template_key_by_id: sop_id → template_key 매핑.
    """

    done_ids: list[int] = []
    key_by_id: dict[int, str] = {}

    valid_payloads = collect_valid_jira_issue_payloads(
        rows=rows,
        config=config,
        project_key_by_id=project_key_by_id,
        template_key_by_id=template_key_by_id,
    )
    for rid, _, payload in valid_payloads:
        try:
            resp = session.post(
                config.create_url,
                json=payload,
                timeout=(config.connect_timeout, config.read_timeout),
            )
        except requests.RequestException:
            logger.exception("Jira create request failed id=%s", rid)
            continue
        if resp.status_code != 201:
            logger.error("Jira create failed id=%s %s: %s", rid, resp.status_code, resp.text[:300])
            continue
        data = safe_json(resp)
        key = data.get("key")
        if isinstance(key, str) and key.strip():
            key_by_id[rid] = key.strip()
        done_ids.append(rid)

    return done_ids, key_by_id


__all__ = [
    "bulk_create_jira_issues",
    "collect_valid_jira_issue_payloads",
    "safe_json",
    "single_create_jira_issues",
]
