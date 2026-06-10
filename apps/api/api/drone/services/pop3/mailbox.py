# =============================================================================
# 모듈: Drone SOP POP3 mailbox transport
# 주요 기능: POP3 접속, 메일 파싱, 제목 필터 공통 처리
# 주요 가정: 삭제 확정/롤백 판단은 상위 수집 orchestration에서 수행합니다.
# =============================================================================
"""Drone SOP POP3 mailbox transport 헬퍼 모듈입니다."""

from __future__ import annotations

import poplib
from email.header import decode_header, make_header
from email.parser import BytesParser
from email.policy import default
from typing import Any, Optional, Sequence

from .config import DroneSopPop3Config

_POP3_MAX_LINE_LENGTH = 10 * 1024 * 1024


class _LongLinePop3Mixin:
    """긴 HTML 라인을 포함한 POP3 응답을 읽기 위한 client mixin입니다."""

    def _getline(self) -> tuple[bytes, int]:
        line = self.file.readline(_POP3_MAX_LINE_LENGTH + 1)
        if len(line) > _POP3_MAX_LINE_LENGTH:
            raise poplib.error_proto("line too long")

        if self._debugging > 1:
            print("*get*", repr(line))
        if not line:
            raise poplib.error_proto("-ERR EOF")

        octets = len(line)
        if line[-2:] == poplib.CRLF:
            return line[:-2], octets
        if line[:1] == poplib.CR:
            return line[1:-1], octets
        return line[:-1], octets


class _LongLinePOP3(_LongLinePop3Mixin, poplib.POP3):
    """POP3 line 제한을 Drone SOP 수집 용도에 맞게 확장한 client입니다."""


class _LongLinePOP3SSL(_LongLinePop3Mixin, poplib.POP3_SSL):
    """SSL POP3 line 제한을 Drone SOP 수집 용도에 맞게 확장한 client입니다."""


def extract_html_from_email(msg: Any) -> Optional[str]:
    """이메일 메시지에서 HTML 본문을 추출합니다.

    인자:
        msg: email.message 객체.

    반환:
        HTML 문자열 또는 None.

    부작용:
        없음. 순수 추출입니다.
    """

    # -------------------------------------------------------------------------
    # 1) 멀티파트 메시지에서 HTML 파트 탐색
    # -------------------------------------------------------------------------
    html = next(
        (part.get_content() for part in msg.walk() if part.get_content_type() == "text/html"),
        None,
    )
    if html:
        return html
    # -------------------------------------------------------------------------
    # 2) 단일 파트 HTML 처리
    # -------------------------------------------------------------------------
    if getattr(msg, "get_content_type", lambda: None)() == "text/html":
        return msg.get_content()
    return None


def decode_header_value(raw_value: Any) -> str:
    """메일 헤더 값을 디코딩합니다.

    인자:
        raw_value: 헤더 원본 값.

    반환:
        디코딩된 문자열.

    부작용:
        없음. 순수 디코딩입니다.
    """

    # -------------------------------------------------------------------------
    # 1) None 처리 및 디코딩 시도
    # -------------------------------------------------------------------------
    if raw_value is None:
        return ""
    try:
        return str(make_header(decode_header(str(raw_value))))
    except Exception:
        return str(raw_value)


def subject_matches(subject: str, include_subjects: Sequence[str]) -> bool:
    """제목이 허용된 prefix로 시작하는지 확인합니다.

    인자:
        subject: 메일 제목.
        include_subjects: 허용 제목 목록.

    반환:
        포함 여부(boolean).

    부작용:
        없음. 순수 비교입니다.
    """

    # -------------------------------------------------------------------------
    # 1) 제목 정규화 및 prefix 매칭
    # -------------------------------------------------------------------------
    normalized_subject = subject.strip().lower()
    if not normalized_subject:
        return False
    for prefix in include_subjects:
        if not isinstance(prefix, str):
            continue
        normalized_prefix = prefix.strip().lower()
        if not normalized_prefix:
            continue
        if normalized_subject.startswith(normalized_prefix):
            return True
    return False


def create_pop3_client(*, config: DroneSopPop3Config) -> Any:
    """설정값으로 POP3 client를 생성합니다."""

    if not config.host or not config.username or not config.password:
        raise ValueError("POP3 connection info is incomplete (host/username/password required)")

    client_cls = _LongLinePOP3SSL if config.use_ssl else _LongLinePOP3
    return client_cls(config.host, config.port, timeout=config.timeout)


def authenticate_pop3_client(*, client: Any, config: DroneSopPop3Config) -> None:
    """POP3 client에 사용자 인증을 수행합니다."""

    client.user(config.username)
    client.pass_(config.password)


def list_pop3_message_numbers(*, client: Any) -> range:
    """POP3 mailbox 메시지 번호 range를 반환합니다."""

    num_msgs = len(client.list()[1])
    return range(1, num_msgs + 1)


def retrieve_pop3_message(*, client: Any, msg_num: int) -> Any:
    """POP3 메시지를 가져와 email.message 객체로 반환합니다."""

    _, lines, _ = client.retr(msg_num)
    return BytesParser(policy=default).parsebytes(b"\r\n".join(lines))


def mark_pop3_message_for_deletion(*, client: Any, msg_num: int) -> None:
    """POP3 메시지를 삭제 대상으로 표시합니다."""

    client.dele(msg_num)


def rollback_pop3_deletions(*, client: Any) -> None:
    """POP3 삭제 표시를 롤백합니다."""

    client.rset()


def close_pop3_client(*, client: Any) -> None:
    """POP3 client 연결을 종료합니다."""

    client.quit()


__all__ = [
    "authenticate_pop3_client",
    "close_pop3_client",
    "create_pop3_client",
    "decode_header_value",
    "extract_html_from_email",
    "list_pop3_message_numbers",
    "mark_pop3_message_for_deletion",
    "retrieve_pop3_message",
    "rollback_pop3_deletions",
    "subject_matches",
]
