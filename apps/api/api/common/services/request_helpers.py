# common/services/request_helpers.py
"""Django 웹 요청/응답 관련 헬퍼 함수 모음."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme


def parse_json_body(request: HttpRequest) -> Optional[Dict[str, Any]]:
    """요청 바디(JSON)를 파싱해 딕셔너리로 반환합니다."""
    try:
        body = request.body.decode("utf-8")
    except UnicodeDecodeError:
        return None
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def extract_bearer_token(request: HttpRequest) -> str:
    """Authorization 헤더에서 토큰 문자열을 추출합니다."""
    auth_header = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION") or ""
    if not isinstance(auth_header, str):
        return ""
    normalized = auth_header.strip()
    if normalized.lower().startswith("bearer "):
        return normalized[7:].strip()
    return normalized


def ensure_airflow_token(request: HttpRequest, *, require_bearer: bool = False) -> JsonResponse | None:
    """AIRFLOW_TRIGGER_TOKEN을 검증하고 실패 시 JsonResponse를 반환합니다."""
    expected = (
        getattr(settings, "AIRFLOW_TRIGGER_TOKEN", "") or os.getenv("AIRFLOW_TRIGGER_TOKEN") or ""
    ).strip()
    if not expected:
        return JsonResponse({"error": "AIRFLOW_TRIGGER_TOKEN not configured"}, status=500)

    if require_bearer:
        auth_header = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION") or ""
        if isinstance(auth_header, str) and auth_header.strip().lower().startswith("bearer "):
            provided = auth_header.strip()[7:].strip()
        else:
            provided = ""
    else:
        provided = extract_bearer_token(request)

    if provided != expected:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    return None


def resolve_frontend_target(
    next_value: Optional[str], *, request: Optional[HttpRequest] = None
) -> str:
    """프론트엔드 베이스 URL과 next 값을 조합해 안전한 리다이렉트를 생성합니다."""
    base = str(getattr(settings, "FRONTEND_BASE_URL", "") or "").strip()
    if not base and request is not None:
        base = request.build_absolute_uri("/").rstrip("/")
    if not base:
        base = "http://localhost"

    base = base.rstrip("/")
    parsed_base = urlparse(base if "://" in base else f"http://{base.lstrip('/')}")
    allowed_hosts = {parsed_base.netloc} if parsed_base.netloc else set()

    if next_value:
        candidate = str(next_value).strip()
        if candidate:
            if url_has_allowed_host_and_scheme(
                candidate, allowed_hosts=allowed_hosts, require_https=False
            ):
                return candidate
            if candidate.startswith("/"):
                trimmed = candidate.lstrip("/")
                return f"{base}/{trimmed}" if trimmed else base
            if "://" not in candidate:
                trimmed = candidate.lstrip("/")
                return f"{base}/{trimmed}" if trimmed else base
    return base

__all__ = [
    "parse_json_body",
    "extract_bearer_token",
    "ensure_airflow_token",
    "resolve_frontend_target",
]
