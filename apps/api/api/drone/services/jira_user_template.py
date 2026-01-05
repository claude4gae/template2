# =============================================================================
# 모듈: 드론 Jira 템플릿/프로젝트 키 서비스
# 주요 함수: upsert_drone_sop_jira_user_template
# 주요 가정: user_sdwt_prod 단위로 단일 행을 관리합니다.
# =============================================================================
"""드론 Jira 템플릿/프로젝트 키 갱신 서비스 모음."""

from __future__ import annotations

from django.db import transaction

from ..models import DroneSopJiraUserTemplate

_UNSET = object()


def upsert_drone_sop_jira_user_template(
    *,
    user_sdwt_prod: str,
    jira_key: str | None | object = _UNSET,
    template_key: str | None | object = _UNSET,
) -> tuple[DroneSopJiraUserTemplate, int]:
    """user_sdwt_prod에 대한 Jira 템플릿/프로젝트 키를 생성 또는 갱신합니다.

    입력:
    - user_sdwt_prod: user_sdwt_prod 식별자
    - jira_key: Jira 프로젝트 키(없으면 None, 미지정 시 _UNSET)
    - template_key: Jira 템플릿 키(없으면 None, 미지정 시 _UNSET)

    반환:
    - (DroneSopJiraUserTemplate, int): (갱신된 엔티티, 갱신 여부)

    부작용:
    - DroneSopJiraUserTemplate upsert 수행

    오류:
    - ValueError: 필수 입력 누락 또는 갱신 대상 없음
    """

    # -----------------------------------------------------------------------------
    # 1) 입력 검증
    # -----------------------------------------------------------------------------
    if not isinstance(user_sdwt_prod, str) or not user_sdwt_prod.strip():
        raise ValueError("user_sdwt_prod is required")
    if jira_key is _UNSET and template_key is _UNSET:
        raise ValueError("jira_key or template_key is required")
    if jira_key is not _UNSET and jira_key is not None and not isinstance(jira_key, str):
        raise ValueError("jira_key must be string or None")
    if template_key is not _UNSET and template_key is not None and not isinstance(template_key, str):
        raise ValueError("template_key must be string or None")

    normalized_user = user_sdwt_prod.strip()

    # -----------------------------------------------------------------------------
    # 2) 행 조회/생성 및 업데이트
    # -----------------------------------------------------------------------------
    with transaction.atomic():
        template, created = DroneSopJiraUserTemplate.objects.select_for_update().get_or_create(
            user_sdwt_prod=normalized_user
        )
        update_fields: list[str] = []
        if jira_key is not _UNSET and template.jira_key != jira_key:
            template.jira_key = jira_key
            update_fields.append("jira_key")
        if template_key is not _UNSET and template.template_key != template_key:
            template.template_key = template_key
            update_fields.append("template_key")

        if update_fields:
            template.save(update_fields=[*update_fields, "updated_at"])
            return template, 1

        if created:
            return template, 1

    return template, 0
