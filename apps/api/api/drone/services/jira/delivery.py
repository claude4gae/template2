# =============================================================================
# 모듈: Drone SOP Jira 전송/템플릿 유틸
# 주요 기능: 템플릿 렌더링, CTTTM URL 보강, Jira 생성 API 호출
# 주요 가정: 이 모듈은 부작용(외부 API 호출/템플릿 캐시)을 포함합니다.
# =============================================================================
"""Drone SOP Jira 전송 보조 유틸리티 모음."""

from __future__ import annotations

from .ctttm import enrich_rows_with_ctttm_urls as _enrich_rows_with_ctttm_urls
from .issue_fields import (
    build_jira_description_html as _build_jira_description_html,
    build_jira_issue_fields as _build_jira_issue_fields,
    build_jira_summary as _build_jira_summary,
)
from .templates.jira_template_registry import SUMMARY_BUILDERS, TEMPLATE_SOURCES
from .transport import (
    bulk_create_jira_issues as _bulk_create_jira_issues,
    collect_valid_jira_issue_payloads as _collect_valid_jira_issue_payloads,
    safe_json as _safe_json,
    single_create_jira_issues as _single_create_jira_issues,
)


__all__ = [
    "_bulk_create_jira_issues",
    "_build_jira_description_html",
    "_build_jira_issue_fields",
    "_build_jira_summary",
    "_enrich_rows_with_ctttm_urls",
    "_single_create_jira_issues",
]
