# =============================================================================
# 모듈 설명: 공용 Knox 메일 발신 API 호출 유틸을 제공합니다.
# - 주요 함수: send_knox_mail_api
# - 불변 조건: MAIL_API_* 환경변수가 필요합니다.
# =============================================================================

from __future__ import annotations

import os
from typing import Any, Dict, Sequence

import requests

_MAIL_API_TIMEOUT_SECONDS = 10


class MailSendError(Exception):
    """사내 메일 발신 API 호출 실패 예외."""


def _read_mail_api_config() -> tuple[str, str, str, str]:
    """메일 API 호출에 필요한 환경변수를 읽어 정규화합니다."""

    url = (os.getenv("MAIL_API_URL") or "").strip()
    prod_key = (os.getenv("MAIL_API_KEY") or "").strip()
    system_id = (os.getenv("MAIL_API_SYSTEM_ID") or "plane").strip()
    knox_id = (os.getenv("MAIL_API_KNOX_ID") or "").strip()
    return url, prod_key, system_id, knox_id


def _normalize_receiver_emails(receiver_emails: Sequence[str]) -> list[str]:
    """수신자 이메일 목록에서 빈 값을 제거합니다."""

    return [str(email).strip() for email in receiver_emails if str(email).strip()]


def _build_mail_payload(
    *,
    sender_email: str,
    receiver_emails: Sequence[str],
    subject: str,
    html_content: str,
) -> Dict[str, Any]:
    """Knox Mail API 요청 payload를 생성합니다."""

    return {
        "receiverList": [
            {"email": email, "recipientType": "TO"} for email in receiver_emails
        ],
        "title": subject,
        "content": html_content,
        "senderMailAddress": sender_email,
    }


def _normalize_mail_response(response: requests.Response) -> Dict[str, Any]:
    """Knox Mail API 응답을 기존 반환 형식으로 정규화합니다."""

    content_type = response.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        data = response.json()
        if isinstance(data, dict):
            return data
        return {"data": data}
    return {"ok": True}


def send_knox_mail_api(
    sender_email: str,
    receiver_emails: Sequence[str],
    subject: str,
    html_content: str,
) -> Dict[str, Any]:
    """사내 Knox 메일 발신 API를 호출해 메일을 발송합니다.

    입력:
        sender_email: 발신자 이메일 주소.
        receiver_emails: 수신자 이메일 목록.
        subject: 메일 제목.
        html_content: HTML 본문.
    반환:
        - JSON 응답이면 dict
        - JSON이 아니면 {"ok": True}
    부작용:
        외부 메일 발신 API에 HTTP 요청을 전송합니다.
    오류:
        - 환경변수 누락 시 MailSendError
        - 수신자 없음 시 MailSendError
        - HTTP 오류/타임아웃 시 MailSendError

    환경변수:
        - MAIL_API_URL: 발신 API URL (예: https://.../send)
        - MAIL_API_KEY: x-dep-ticket 값
        - MAIL_API_SYSTEM_ID: systemId (기본값: plane)
        - MAIL_API_KNOX_ID: loginUser.login 값
    """

    # -----------------------------------------------------------------------------
    # 1) 환경변수 및 입력값 검증
    # -----------------------------------------------------------------------------
    url, prod_key, system_id, knox_id = _read_mail_api_config()
    if not url:
        raise MailSendError("MAIL_API_URL 미설정")
    if not prod_key or not knox_id:
        raise MailSendError("MAIL_API_KEY / MAIL_API_KNOX_ID 미설정")

    normalized_receivers = _normalize_receiver_emails(receiver_emails)
    if not normalized_receivers:
        raise MailSendError("수신자 없음")

    # -----------------------------------------------------------------------------
    # 2) 요청 파라미터 구성
    # -----------------------------------------------------------------------------
    params = {"systemId": system_id, "loginUser.login": knox_id}
    headers = {"x-dep-ticket": prod_key}
    payload = _build_mail_payload(
        sender_email=sender_email,
        receiver_emails=normalized_receivers,
        subject=subject,
        html_content=html_content,
    )

    # -----------------------------------------------------------------------------
    # 3) API 호출 및 응답 처리
    # -----------------------------------------------------------------------------
    try:
        response = requests.post(
            url,
            params=params,
            headers=headers,
            json=payload,
            timeout=_MAIL_API_TIMEOUT_SECONDS,
        )
        if not response.ok:
            raise MailSendError(
                f"메일 API 오류 {response.status_code}: {response.text[:300]}"
            )
        return _normalize_mail_response(response)
    except requests.Timeout as exc:
        raise MailSendError("메일 API 타임아웃") from exc
    except requests.RequestException as exc:
        raise MailSendError(f"메일 API 요청 실패: {exc}") from exc
