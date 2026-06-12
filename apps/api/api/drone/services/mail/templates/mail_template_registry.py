# =============================================================================
# 모듈 설명: Drone SOP 메일 템플릿 정의를 등록합니다.
# - 주요 대상: MAIL_TEMPLATE_SOURCES, MAIL_SUBJECT_BUILDERS
# - 불변 조건: 템플릿 키는 사전에 정의된 문자열이어야 함
# =============================================================================

"""Drone SOP 메일 템플릿 레지스트리 모음."""
from __future__ import annotations

from .mail_template_auto_sp import (
    BODY_TEMPLATE as AUTO_SP_BODY_TEMPLATE,
    TEMPLATE_KEY as AUTO_SP_KEY,
    build_subject as build_auto_sp_subject,
)
from .mail_template_common import BODY_TEMPLATE as COMMON_BODY_TEMPLATE, TEMPLATE_KEY as COMMON_KEY
from .mail_template_common import build_subject as build_common_subject
from .mail_template_h1 import BODY_TEMPLATE as H1_BODY_TEMPLATE, TEMPLATE_KEY as H1_KEY
from .mail_template_h1 import build_subject as build_h1_subject

MAIL_TEMPLATE_SOURCES = {
    COMMON_KEY: COMMON_BODY_TEMPLATE,
    H1_KEY: H1_BODY_TEMPLATE,
    AUTO_SP_KEY: AUTO_SP_BODY_TEMPLATE,
}

MAIL_SUBJECT_BUILDERS = {
    COMMON_KEY: build_common_subject,
    H1_KEY: build_h1_subject,
    AUTO_SP_KEY: build_auto_sp_subject,
}

__all__ = ["MAIL_SUBJECT_BUILDERS", "MAIL_TEMPLATE_SOURCES"]
