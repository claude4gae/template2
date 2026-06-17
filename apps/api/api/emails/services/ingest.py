# =============================================================================
# 모듈 설명: POP3 메일 수집 및 메시지 파싱/저장을 담당합니다.
# - 주요 기능: 메일 파싱, POP3 수집, RAG 인덱싱 요청
# - 불변 조건: 제목 제외 규칙을 최우선 적용하고 message_id를 중복 방지 키로 사용합니다.
# =============================================================================

from __future__ import annotations

import hashlib
import logging
import os
import poplib
from datetime import datetime
from email.header import decode_header, make_header
from email.message import Message
from email.parser import BytesParser
from email.policy import default
from email.utils import getaddresses, parseaddr, parsedate_to_datetime
from typing import Any, Dict, Iterable, List, Tuple

from django.utils import timezone

from api.common.services import UNASSIGNED_USER_SDWT_PROD

from ..models import Email
from ..selectors import resolve_email_affiliation
from .rag import enqueue_rag_index, register_missing_rag_docs
from .storage import save_parsed_email, store_email_html_and_assets
from .utils import _normalize_participants

# =============================================================================
# 로깅
# =============================================================================
logger = logging.getLogger(__name__)

# =============================================================================
# 상수
# =============================================================================
DEFAULT_EXCLUDED_SUBJECT_PREFIXES = ("[drone_sop]", "[test]")
EXCLUDED_BODY_ELEMENT_IDS = {
    "standardsignature",
    "bannersignimg",
    "confidentialsignimg",
}
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
    """POP3 line 제한을 emails 수집 용도에 맞게 확장한 client입니다."""


class _LongLinePOP3SSL(_LongLinePop3Mixin, poplib.POP3_SSL):
    """SSL POP3 line 제한을 emails 수집 용도에 맞게 확장한 client입니다."""


def _load_excluded_subject_prefixes() -> tuple[str, ...]:
    """환경변수 기반 메일 제목 제외 prefix 목록을 로드합니다.

    입력:
        없음(환경변수 EMAIL_EXCLUDED_SUBJECT_PREFIXES 사용).
    반환:
        제외 prefix 튜플.
    부작용:
        환경변수 읽기.
    오류:
        없음.
    """

    # -----------------------------------------------------------------------------
    # 1) 환경변수 조회
    # -----------------------------------------------------------------------------
    raw = os.getenv("EMAIL_EXCLUDED_SUBJECT_PREFIXES", "")
    if not raw:
        return DEFAULT_EXCLUDED_SUBJECT_PREFIXES

    # -----------------------------------------------------------------------------
    # 2) 목록 파싱 및 정규화
    # -----------------------------------------------------------------------------
    prefixes: List[str] = []
    for item in raw.split(","):
        cleaned = item.strip().strip("\"'").lower()
        if cleaned:
            prefixes.append(cleaned)

    # -----------------------------------------------------------------------------
    # 3) 기본값 폴백
    # -----------------------------------------------------------------------------
    return tuple(prefixes) if prefixes else DEFAULT_EXCLUDED_SUBJECT_PREFIXES


# 상수: 환경변수 반영 결과
EXCLUDED_SUBJECT_PREFIXES = _load_excluded_subject_prefixes()


def _is_excluded_subject(subject: str) -> bool:
    """제목이 제외 대상 prefix로 시작하는지 검사합니다.

    입력:
        subject: 메일 제목 문자열.
    반환:
        제외 대상이면 True.
    부작용:
        없음.
    오류:
        없음.
    """

    # -----------------------------------------------------------------------------
    # 1) 문자열 정규화 및 prefix 검사
    # -----------------------------------------------------------------------------
    normalized = (subject or "").strip().lower()
    return any(normalized.startswith(prefix) for prefix in EXCLUDED_SUBJECT_PREFIXES)


def _decode_header_value(raw_value: str | None) -> str:
    """RFC2047 인코딩 헤더 값을 사람이 읽을 수 있는 문자열로 디코딩합니다.

    입력:
        raw_value: 원본 헤더 값.
    반환:
        디코딩된 문자열(실패 시 원문).
    부작용:
        없음.
    오류:
        디코딩 실패 시 원문 반환.
    """

    # -----------------------------------------------------------------------------
    # 1) 빈 값 처리
    # -----------------------------------------------------------------------------
    if not raw_value:
        return ""

    # -----------------------------------------------------------------------------
    # 2) RFC2047 디코딩
    # -----------------------------------------------------------------------------
    try:
        return str(make_header(decode_header(raw_value)))
    except Exception:
        return raw_value


def _format_display_address(*, name: str, address: str) -> str:
    """(name, address) 튜플을 사람이 읽기 좋은 형식으로 정규화합니다.

    입력:
        name: 표시 이름.
        address: 이메일 주소.
    반환:
        "Name <addr>" 또는 주소/이름 문자열.
    부작용:
        없음.
    오류:
        없음.
    """

    # -----------------------------------------------------------------------------
    # 1) 표시 이름/주소 정규화
    # -----------------------------------------------------------------------------
    normalized_name = " ".join(str(name or "").split()).strip()
    normalized_address = str(address or "").strip()
    if normalized_name and normalized_address:
        return f"{normalized_name} <{normalized_address}>"
    return normalized_address or normalized_name


def _extract_participants(msg: Message, header_name: str) -> list[str]:
    """메일 헤더(To/Cc 등)에서 수신자 리스트를 파싱해 반환합니다.

    입력:
        msg: 이메일 Message 객체.
        header_name: 헤더 이름("To", "Cc" 등).
    반환:
        정규화된 참여자 문자열 리스트.
    부작용:
        없음.
    오류:
        없음.
    """

    # -----------------------------------------------------------------------------
    # 1) 헤더 값 디코딩 및 파싱
    # -----------------------------------------------------------------------------
    raw_values = msg.get_all(header_name, []) or []
    decoded_values = [_decode_header_value(value) for value in raw_values if value]
    parsed = getaddresses(decoded_values)

    # -----------------------------------------------------------------------------
    # 2) 표시 문자열 구성 및 정규화
    # -----------------------------------------------------------------------------
    results: list[str] = []
    for name, address in parsed:
        formatted = _format_display_address(name=name, address=address)
        if formatted:
            results.append(formatted)
    return _normalize_participants(results)


def _decode_part(part: Message) -> str:
    """메일 MIME 파트의 payload를 charset 기반으로 문자열 디코딩합니다.

    입력:
        part: MIME Message 파트.
    반환:
        디코딩된 문자열(없으면 빈 문자열).
    부작용:
        없음.
    오류:
        charset 미지원 시 UTF-8로 폴백.
    """

    # -----------------------------------------------------------------------------
    # 1) payload 추출
    # -----------------------------------------------------------------------------
    payload = part.get_payload(decode=True)
    if payload is None:
        return ""
    charset = part.get_content_charset() or "utf-8"

    # -----------------------------------------------------------------------------
    # 2) charset 기반 디코딩
    # -----------------------------------------------------------------------------
    try:
        return payload.decode(charset, errors="replace")
    except LookupError:
        return payload.decode("utf-8", errors="replace")


def _replace_mosaic_embeds(soup: Any) -> None:
    """모자이크(https://mosaic...) embed를 링크로 치환해 렌더링 문제를 완화합니다.

    입력:
        soup: BeautifulSoup 객체.
    반환:
        없음.
    부작용:
        soup 객체를 직접 수정.
    오류:
        없음.
    """

    # -----------------------------------------------------------------------------
    # 1) 모자이크 embed 태그 치환
    # -----------------------------------------------------------------------------
    for embed in soup.find_all("embed"):
        src = embed.get("src", "")
        if not src.startswith("https://mosaic"):
            continue
        parent_div = embed.find_parent("div")
        if parent_div:
            span_tag = soup.new_tag("span")
            a_tag = soup.new_tag("a", href=src)
            a_tag.string = "모자이크 링크"
            span_tag.append(a_tag)
            parent_div.replace_with(span_tag)


def _remove_excluded_body_elements(soup: Any) -> None:
    """HTML 본문에서 제외 대상 요소를 제거합니다.

    입력:
        soup: BeautifulSoup 객체.
    반환:
        없음.
    부작용:
        soup 객체에서 제외 대상 요소를 제거.
    오류:
        없음.
    """

    # -----------------------------------------------------------------------------
    # 1) ID 기준 제거
    # -----------------------------------------------------------------------------
    for element in soup.find_all(attrs={"id": True}):
        element_id = str(element.get("id") or "").strip().lower()
        if element_id in EXCLUDED_BODY_ELEMENT_IDS:
            element.decompose()


def _remove_excluded_markers_from_text(text: str) -> str:
    """본문 텍스트에서 제외 대상 ID 문자열이 포함된 라인을 제거합니다.

    입력:
        text: 본문 텍스트 문자열.
    반환:
        제외 대상 라인이 제거된 텍스트.
    부작용:
        없음.
    오류:
        없음.
    """

    # -----------------------------------------------------------------------------
    # 1) 빈 값 처리
    # -----------------------------------------------------------------------------
    if not text:
        return ""

    # -----------------------------------------------------------------------------
    # 2) 라인 필터링
    # -----------------------------------------------------------------------------
    cleaned_lines: List[str] = []
    for line in text.splitlines():
        lowered = line.lower()
        if any(marker in lowered for marker in EXCLUDED_BODY_ELEMENT_IDS):
            continue
        cleaned_lines.append(line)

    # -----------------------------------------------------------------------------
    # 3) 결과 반환
    # -----------------------------------------------------------------------------
    return "\n".join(cleaned_lines)


def _extract_bodies(msg: Message) -> Tuple[str, str, Dict[str, Dict[str, Any]]]:
    """메일 메시지에서 텍스트/HTML 본문을 추출하고 정규화합니다.

    입력:
        msg: 이메일 Message 객체.
    반환:
        (body_text, body_html, cid_map) 튜플.
    부작용:
        없음.
    오류:
        HTML 파싱 실패 시 원문 텍스트로 폴백.
    """

    # -----------------------------------------------------------------------------
    # 1) 초기값 준비
    # -----------------------------------------------------------------------------
    text_body = ""
    html_content = ""
    cid_map: Dict[str, Dict[str, Any]] = {}

    # -----------------------------------------------------------------------------
    # 2) 멀티파트 메시지 처리
    # -----------------------------------------------------------------------------
    if msg.is_multipart():
        for part in msg.walk():
            if part.is_multipart():
                continue
            content_type = part.get_content_type()
            disposition = (part.get("Content-Disposition") or "").lower()
            content_id = part.get("Content-ID")

            if content_type.startswith("image/") and content_id:
                payload = part.get_payload(decode=True)
                if payload:
                    cid_map[content_id.strip("<>")] = {
                        "data": payload,
                        "content_type": content_type,
                    }
                continue

            if disposition.startswith("attachment"):
                continue

            if content_type == "text/plain" and not text_body:
                text_body = _decode_part(part)
            elif content_type == "text/html" and not html_content:
                html_content = _decode_part(part)

    # -----------------------------------------------------------------------------
    # 3) 단일 파트 메시지 처리
    # -----------------------------------------------------------------------------
    else:
        content_type = msg.get_content_type()
        disposition = (msg.get("Content-Disposition") or "").lower()
        content_id = msg.get("Content-ID")

        if content_type.startswith("image/") and content_id:
            payload = msg.get_payload(decode=True)
            if payload:
                cid_map[content_id.strip("<>")] = {
                    "data": payload,
                    "content_type": content_type,
                }

        if not disposition.startswith("attachment"):
            if content_type == "text/plain":
                text_body = _decode_part(msg)
            elif content_type == "text/html":
                html_content = _decode_part(msg)

    # -----------------------------------------------------------------------------
    # 4) HTML 정규화 및 텍스트 추출
    # -----------------------------------------------------------------------------
    if html_content:
        from bs4 import BeautifulSoup  # 인제스트 전용 의존성

        soup = BeautifulSoup(html_content, "lxml")
        _remove_excluded_body_elements(soup)
        _replace_mosaic_embeds(soup)
        body_html = soup.prettify()
        body_text = _remove_excluded_markers_from_text(soup.get_text())
        return body_text, body_html, cid_map

    # -----------------------------------------------------------------------------
    # 5) 텍스트 본문 폴백 처리
    # -----------------------------------------------------------------------------
    if not text_body and hasattr(msg, "get_body"):
        try:
            fallback = msg.get_body(preferencelist=("plain", "html"))
            if fallback:
                text_body = _decode_part(fallback)
        except Exception:
            pass

    # -----------------------------------------------------------------------------
    # 6) 기본 반환
    # -----------------------------------------------------------------------------
    return _remove_excluded_markers_from_text(text_body or ""), "", cid_map


def _parse_received_at(msg: Message) -> datetime:
    """메일 Date 헤더를 파싱해 수신 시각(timezone-aware)을 반환합니다.

    입력:
        msg: 이메일 Message 객체.
    반환:
        timezone-aware 수신 시각.
    부작용:
        없음.
    오류:
        파싱 실패 시 현재 시각 반환.
    """

    # -----------------------------------------------------------------------------
    # 1) Date 헤더 파싱
    # -----------------------------------------------------------------------------
    raw_date = msg.get("Date")
    if raw_date:
        try:
            parsed = parsedate_to_datetime(raw_date)
            if parsed and timezone.is_naive(parsed):
                parsed = timezone.make_aware(parsed, timezone.utc)
            if parsed:
                return parsed
        except Exception:
            logger.exception("Failed to parse email Date header: %s", raw_date)

    # -----------------------------------------------------------------------------
    # 2) 폴백 시각 반환
    # -----------------------------------------------------------------------------
    return timezone.now()


def _extract_subject_header(msg: Message) -> str:
    """메일 Subject 헤더를 디코딩해 반환합니다.

    입력:
        msg: 이메일 Message 객체.
    반환:
        디코딩된 제목 문자열.
    부작용:
        없음.
    오류:
        디코딩 실패 시 원문 반환.
    """

    # -----------------------------------------------------------------------------
    # 1) 제목 디코딩
    # -----------------------------------------------------------------------------
    return _decode_header_value(msg.get("Subject"))


def _extract_sender_id(sender: str) -> str:
    """발신자 주소 문자열에서 sender_id(로컬파트)를 추출합니다.

    입력:
        sender: 발신자 표시 문자열.
    반환:
        sender_id 문자열(없으면 UNKNOWN).
    부작용:
        없음.
    오류:
        없음.
    """

    # -----------------------------------------------------------------------------
    # 1) 이메일 주소 파싱
    # -----------------------------------------------------------------------------
    address = parseaddr(sender or "")[1]
    if address and "@" in address:
        local = address.split("@", 1)[0].strip()
        if local:
            return local

    # -----------------------------------------------------------------------------
    # 2) 폴백 처리
    # -----------------------------------------------------------------------------
    normalized = (sender or "").strip()
    return normalized or "UNKNOWN"


def _parse_message_to_fields(msg: Message) -> Dict[str, Any]:
    """메일 Message 객체를 Email 저장에 필요한 필드 dict로 변환합니다.

    입력:
        msg: 이메일 Message 객체.
    반환:
        Email 저장에 필요한 필드 dict(cid_map 포함).
    부작용:
        없음.
    오류:
        없음(필수값 부족 시 기본값 생성).
    """

    # -----------------------------------------------------------------------------
    # 1) 기본 헤더/참여자 파싱
    # -----------------------------------------------------------------------------
    subject = _extract_subject_header(msg)
    sender = _decode_header_value(msg.get("From"))
    recipient = _extract_participants(msg, "To") or _extract_participants(msg, "Delivered-To")
    cc = _extract_participants(msg, "Cc")
    message_id = (msg.get("Message-ID") or msg.get("Message-Id") or "").strip()
    if not message_id:
        content_hash = hashlib.sha256(msg.as_bytes()).hexdigest()
        message_id = f"generated-{content_hash}"

    # -----------------------------------------------------------------------------
    # 2) 본문/시각/발신자 정보 추출
    # -----------------------------------------------------------------------------
    body_text, body_html, cid_map = _extract_bodies(msg)
    received_at = _parse_received_at(msg)
    sender_id = _extract_sender_id(sender)

    # -----------------------------------------------------------------------------
    # 3) 필드 dict 구성
    # -----------------------------------------------------------------------------
    return {
        "message_id": message_id,
        "received_at": received_at,
        "subject": subject,
        "sender": sender,
        "sender_id": sender_id,
        "recipient": recipient,
        "cc": cc,
        "body_text": body_text,
        "body_html": body_html,
        "cid_map": cid_map,
    }


def _iter_pop3_messages(session: Any) -> Iterable[Tuple[int, Message]]:
    """POP3 세션에서 (메시지 번호, Message) 스트림을 생성합니다.

    입력:
        session: POP3 세션 객체.
    반환:
        (메시지 번호, Message) 이터레이터.
    부작용:
        POP3 서버에 LIST/RETR 요청을 수행할 수 있음.
    오류:
        POP3 세션 오류는 상위로 전파.
    """

    # -----------------------------------------------------------------------------
    # 1) 세션 제공 이터레이터 사용
    # -----------------------------------------------------------------------------
    if hasattr(session, "iter_messages"):
        yield from session.iter_messages()
        return

    # -----------------------------------------------------------------------------
    # 2) LIST/RETR 기반 수집
    # -----------------------------------------------------------------------------
    _resp, items, _octets = session.list()
    if not items:
        return

    for item in items:
        raw = item.decode() if isinstance(item, (bytes, bytearray)) else str(item)
        msg_num = int(raw.split()[0])
        _resp, lines, _octets = session.retr(msg_num)
        raw_msg = b"\n".join(lines)
        msg = BytesParser(policy=default).parsebytes(raw_msg)
        yield msg_num, msg


def _delete_pop3_messages(session: Any, message_numbers: List[int]) -> None:
    """POP3 세션에서 지정한 메시지 번호들을 삭제(mark)합니다.

    입력:
        session: POP3 세션 객체.
        message_numbers: 삭제할 메시지 번호 리스트.
    반환:
        없음.
    부작용:
        POP3 서버에 DELE 요청을 수행합니다.
    오류:
        삭제 실패는 로깅 후 무시합니다.
    """

    # -----------------------------------------------------------------------------
    # 1) 입력 검증
    # -----------------------------------------------------------------------------
    if not message_numbers:
        return

    # -----------------------------------------------------------------------------
    # 2) 삭제 마킹 수행
    # -----------------------------------------------------------------------------
    for msg_num in message_numbers:
        try:
            session.dele(msg_num)
        except Exception:
            logger.exception("Failed to delete POP3 message #%s", msg_num)


def ingest_pop3_mailbox(session: Any) -> List[int]:
    """POP3 메일함을 순회하며 저장/인덱싱 후 삭제 대상 번호를 반환합니다.

    입력:
        session: POP3 세션 객체.
    반환:
        삭제 처리 대상 메시지 번호 리스트.
    부작용:
        - Email 저장 및 RAG 인덱싱 Outbox 적재.
        - POP3 DELE 마킹.
    오류:
        개별 메시지 처리 오류는 로깅 후 다음 메시지로 진행.
    """

    # -----------------------------------------------------------------------------
    # 1) 삭제 대상 초기화
    # -----------------------------------------------------------------------------
    to_delete: List[int] = []

    # -----------------------------------------------------------------------------
    # 2) 메시지 순회 및 저장 처리
    # -----------------------------------------------------------------------------
    for msg_num, msg in _iter_pop3_messages(session):
        try:
            subject = _extract_subject_header(msg)
            if _is_excluded_subject(subject):
                logger.info("Skipping excluded email subject: %s", subject)
                continue

            fields = _parse_message_to_fields(msg)
            sender_id = fields["sender_id"]
            received_at = fields["received_at"]
            affiliation = resolve_email_affiliation(sender_id=sender_id, received_at=received_at)
            user_sdwt_prod = affiliation["user_sdwt_prod"]
            classification_source = affiliation["classification_source"]
            rag_index_status = (
                Email.RagIndexStatus.PENDING
                if classification_source == Email.ClassificationSource.CONFIRMED_USER
                else Email.RagIndexStatus.SKIPPED
            )

            email_obj, created = save_parsed_email(
                message_id=fields["message_id"],
                received_at=received_at,
                subject=fields["subject"],
                sender=fields["sender"],
                sender_id=sender_id,
                recipient=fields["recipient"],
                cc=fields["cc"],
                user_sdwt_prod=user_sdwt_prod,
                classification_source=classification_source,
                rag_index_status=rag_index_status,
                body_text=fields.get("body_text") or "",
            )

            to_delete.append(msg_num)

            # 신규 저장이거나 HTML 키가 없으면 MinIO 저장을 재시도합니다.
            if created or not email_obj.body_html_object_key:
                try:
                    store_email_html_and_assets(
                        email=email_obj,
                        body_html=fields.get("body_html"),
                        cid_map=fields.get("cid_map"),
                    )
                except Exception:
                    logger.exception("Failed to store email HTML/assets (id=%s)", email_obj.id)

            if (
                not email_obj.rag_doc_id
                and email_obj.user_sdwt_prod != UNASSIGNED_USER_SDWT_PROD
                and email_obj.classification_source == Email.ClassificationSource.CONFIRMED_USER
                and email_obj.rag_index_status == Email.RagIndexStatus.PENDING
            ):
                try:
                    enqueue_rag_index(email=email_obj)
                except Exception:
                    logger.exception("Failed to enqueue RAG outbox for email %s", email_obj.id)

        except Exception as exc:
            logger.exception("Failed to process POP3 message #%s: %s", msg_num, exc)
            continue

    # -----------------------------------------------------------------------------
    # 3) 삭제 마킹 및 결과 반환
    # -----------------------------------------------------------------------------
    _delete_pop3_messages(session, to_delete)
    return to_delete


def run_pop3_ingest(
    *,
    host: str,
    port: int,
    username: str,
    password: str,
    use_ssl: bool = True,
    timeout: int = 60,
) -> Dict[str, int]:
    """POP3 세션을 열어 메일을 수집/저장하고 삭제를 커밋합니다.

    입력:
        host: POP3 서버 호스트.
        port: POP3 포트.
        username: 로그인 사용자.
        password: 로그인 비밀번호.
        use_ssl: True면 POP3_SSL 사용.
        timeout: 소켓 타임아웃(초).
    반환:
        {"deleted": 삭제된 메시지 수, "reindexed": 백필 재등록 수}
    부작용:
        - POP3 메일함 읽기/삭제 처리
        - Email 저장 및 RAG 인덱싱 요청
    오류:
        - 연결 정보 누락 시 ValueError
        - POP3/네트워크 오류는 상위로 전파
    """

    # -----------------------------------------------------------------------------
    # 1) 입력 검증
    # -----------------------------------------------------------------------------
    if not host or not username or not password:
        raise ValueError("POP3 connection info is incomplete (host/username/password required)")

    # -----------------------------------------------------------------------------
    # 2) 클라이언트 생성 및 로그인
    # -----------------------------------------------------------------------------
    client_cls = _LongLinePOP3SSL if use_ssl else _LongLinePOP3
    client = client_cls(host, port, timeout=timeout)
    deleted: List[int] = []
    reindexed = 0
    try:
        client.user(username)
        client.pass_(password)
        logger.info("POP3 login succeeded: host=%s port=%s ssl=%s", host, port, use_ssl)

        # -----------------------------------------------------------------------------
        # 3) 수집/백필 처리
        # -----------------------------------------------------------------------------
        deleted = ingest_pop3_mailbox(client) or []
        try:
            reindexed = register_missing_rag_docs()
            if reindexed:
                logger.info("RAG backfill attempted for %s emails without rag_doc_id", reindexed)
        except Exception:
            logger.exception("RAG backfill failed after POP3 ingest")
        logger.info("Ingest complete; marked %s messages for deletion", len(deleted))

        client.quit()
        logger.info("POP3 session closed (quit)")
    except Exception:
        logger.exception("POP3 ingest failed; rolling back via rset()")
        try:
            client.rset()
        except Exception:
            logger.debug("POP3 rset failed")
        raise
    finally:
        try:
            client.quit()
        except Exception:
            pass

    # -----------------------------------------------------------------------------
    # 4) 결과 반환
    # -----------------------------------------------------------------------------
    return {"deleted": len(deleted), "reindexed": reindexed}


def _env_bool(key: str, default: bool = False) -> bool:
    """환경변수 값을 boolean으로 파싱합니다.

    입력:
        key: 환경변수 키.
        default: 미설정 시 기본값.
    반환:
        해석된 boolean 값.
    부작용:
        환경변수 읽기.
    오류:
        없음.
    """

    # -----------------------------------------------------------------------------
    # 1) 환경변수 조회 및 해석
    # -----------------------------------------------------------------------------
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def run_pop3_ingest_from_env() -> Dict[str, int]:
    """환경변수로 POP3 수집을 실행합니다.

    입력:
        없음(환경변수 사용).
    반환:
        {"deleted": 삭제된 메시지 수, "reindexed": 백필 재등록 수}
    부작용:
        POP3 메일함 접근 및 Email 저장 수행.
    오류:
        환경변수 미설정 시 ValueError가 발생할 수 있음.

    환경변수(우선):
        - EMAIL_POP3_HOST / EMAIL_POP3_PORT / EMAIL_POP3_USERNAME / EMAIL_POP3_PASSWORD (우선 사용)
        - EMAIL_POP3_USE_SSL / EMAIL_POP3_TIMEOUT (우선 사용)
    폴백:
        - POP3_HOST / POP3_PORT / POP3_USERNAME / POP3_PASSWORD / POP3_USE_SSL / POP3_TIMEOUT (폴백 사용)
    """

    # -----------------------------------------------------------------------------
    # 1) 환경변수 읽기
    # -----------------------------------------------------------------------------
    host = os.getenv("EMAIL_POP3_HOST") or os.getenv("POP3_HOST") or ""
    port = int(os.getenv("EMAIL_POP3_PORT") or os.getenv("POP3_PORT") or "995")
    username = os.getenv("EMAIL_POP3_USERNAME") or os.getenv("POP3_USERNAME") or ""
    password = os.getenv("EMAIL_POP3_PASSWORD") or os.getenv("POP3_PASSWORD") or ""
    use_ssl = _env_bool("EMAIL_POP3_USE_SSL", _env_bool("POP3_USE_SSL", True))
    timeout = int(os.getenv("EMAIL_POP3_TIMEOUT") or os.getenv("POP3_TIMEOUT") or "60")

    # -----------------------------------------------------------------------------
    # 2) 수집 실행
    # -----------------------------------------------------------------------------
    return run_pop3_ingest(
        host=host,
        port=port,
        username=username,
        password=password,
        use_ssl=use_ssl,
        timeout=timeout,
    )
