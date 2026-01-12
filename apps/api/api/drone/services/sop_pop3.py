# =============================================================================
# 모듈: Drone SOP POP3 수집 서비스
# 주요 기능: POP3/더미 메일 수집, SOP upsert, 정리 작업
# 주요 가정: 오프라인 개발은 더미 메일 API로 대체합니다.
# =============================================================================
"""Drone SOP POP3 수집 헬퍼 모듈입니다."""

from __future__ import annotations

import fnmatch
import json
import logging
import os
import poplib
from dataclasses import dataclass
from datetime import timedelta
from email.header import decode_header, make_header
from email.parser import BytesParser
from email.policy import default
from typing import Any, Optional, Sequence

import requests
from bs4 import BeautifulSoup

from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone

from .. import selectors
from ..models import DroneSOP, build_sop_key
from .utils import (
    _first_defined,
    _lock_key,
    _parse_bool,
    _parse_int,
    _release_advisory_lock,
    _try_advisory_lock,
)

logger = logging.getLogger(__name__)


def _normalize_blank(value: Any) -> Any:
    """빈 문자열을 None으로 정규화합니다.

    인자:
        value: 원본 값.

    반환:
        None 또는 원본/변환 값.

    부작용:
        없음. 순수 정규화입니다.
    """

    # -------------------------------------------------------------------------
    # 1) None/빈 문자열 처리
    # -------------------------------------------------------------------------
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return value


def _sanitize_defect_url(value: Any) -> str | None:
    """결함 URL 값을 정규화합니다.

    인자:
        value: 원본 URL 값.

    반환:
        정규화된 URL 또는 None.

    부작용:
        없음. 순수 정규화입니다.
    """

    # -------------------------------------------------------------------------
    # 1) 문자열 정리 및 따옴표 제거
    # -------------------------------------------------------------------------
    if value is None:
        return None
    cleaned = str(value).replace('"', "").strip()
    return cleaned or None


def _extract_first_data_tag(html: str) -> dict[str, str]:
    """HTML에서 첫 번째 <data> 태그의 자식 정보를 추출합니다.

    인자:
        html: HTML 문자열.

    반환:
        태그명 → 텍스트 값을 담은 dict.

    부작용:
        없음. 파싱만 수행합니다.
    """

    # -------------------------------------------------------------------------
    # 1) HTML 파싱 및 data 태그 탐색
    # -------------------------------------------------------------------------
    soup = BeautifulSoup(html, "html.parser")
    data = soup.find("data")
    if not data:
        return {}
    # -------------------------------------------------------------------------
    # 2) 직계 자식 태그 텍스트 추출
    # -------------------------------------------------------------------------
    parsed: dict[str, str] = {}
    for child in data.find_all(recursive=False):
        if not child.name:
            continue
        parsed[str(child.name).lower()] = child.get_text(strip=True)
    return parsed


def _strip_prefix_num(value: Optional[str]) -> Optional[int]:
    """접두사 2자를 제외한 숫자 부분을 정수로 변환합니다.

    인자:
        value: 접두사가 포함된 문자열.

    반환:
        숫자 부분 정수 또는 None.

    부작용:
        없음. 순수 파싱입니다.
    """

    # -------------------------------------------------------------------------
    # 1) 길이/형식 검증
    # -------------------------------------------------------------------------
    if not value or len(value) <= 2:
        return None
    numeric = value[2:]
    return int(numeric) if numeric.isdigit() else None


def _as_int_bool(value: Any) -> int:
    """불리언 값을 0/1 정수로 변환합니다.

    인자:
        value: 원본 값.

    반환:
        1(True) 또는 0(False).

    부작용:
        없음. 순수 변환입니다.
    """

    return 1 if bool(value) else 0


@dataclass(frozen=True)
class NeedToSendRule:
    """needtosend 계산을 user_sdwt_prod 패턴 기준으로 오버라이드하는 규칙."""

    pattern: str
    comment_last_at: str
    ignore_sample_type: bool = False

    def matches(self, user_sdwt_prod: str) -> bool:
        """패턴 매칭 여부를 반환합니다.

        인자:
            user_sdwt_prod: 사용자 소속 문자열.

        반환:
            패턴 일치 여부.

        부작용:
            없음. 순수 매칭입니다.
        """

        return fnmatch.fnmatch(user_sdwt_prod, self.pattern)

    def compute(self, row: dict[str, Any]) -> int:
        """규칙에 따라 needtosend 값을 계산합니다.

        인자:
            row: Drone SOP 행 dict(행 데이터).

        반환:
            needtosend 값(0/1).

        부작용:
            없음. 순수 계산입니다.
        """

        # ---------------------------------------------------------------------
        # 1) 댓글/마지막 태그 추출
        # ---------------------------------------------------------------------
        comment = str(row.get("comment") or "").strip()
        last_at = comment.split("@")[-1] if comment else ""
        # ---------------------------------------------------------------------
        # 2) 샘플 타입 조건 처리
        # ---------------------------------------------------------------------
        if not self.ignore_sample_type:
            sample_type = str(row.get("sample_type") or "").strip()
            if sample_type == "ENGR_PRODUCTION":
                return 0
        # ---------------------------------------------------------------------
        # 3) 규칙 비교 결과 반환
        # ---------------------------------------------------------------------
        return _as_int_bool(last_at == self.comment_last_at)


def _parse_needtosend_rules(value: Any) -> list[NeedToSendRule]:
    """DRONE_SOP_NEEDTOSEND_RULES 설정을 파싱합니다.

    인자:
        value: JSON 문자열 또는 dict 리스트.

    반환:
        NeedToSendRule 리스트.

    부작용:
        없음. 순수 파싱입니다.

    오류:
        JSON 형식이 아니거나 배열이 아니면 ValueError를 발생시킵니다.
    """

    # -------------------------------------------------------------------------
    # 1) 빈 입력 처리
    # -------------------------------------------------------------------------
    if value is None:
        return []

    # -------------------------------------------------------------------------
    # 2) JSON 문자열 파싱
    # -------------------------------------------------------------------------
    parsed: Any = value
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("DRONE_SOP_NEEDTOSEND_RULES must be a valid JSON array") from exc

    # -------------------------------------------------------------------------
    # 3) 배열 검증
    # -------------------------------------------------------------------------
    if not isinstance(parsed, list):
        raise ValueError("DRONE_SOP_NEEDTOSEND_RULES must be a JSON array of objects")

    # -------------------------------------------------------------------------
    # 4) 규칙 객체 구성
    # -------------------------------------------------------------------------
    rules: list[NeedToSendRule] = []
    for entry in parsed:
        if not isinstance(entry, dict):
            continue
        pattern = str(entry.get("pattern") or entry.get("glob") or "").strip()
        comment_last_at = str(
            entry.get("comment_last_at")
            or entry.get("commentLastAt")
            or entry.get("lastAt")
            or entry.get("expected")
            or ""
        ).strip()
        if not pattern or not comment_last_at:
            continue
        ignore_sample_type = bool(entry.get("ignore_sample_type") or entry.get("ignoreSampleType") or False)
        rules.append(
            NeedToSendRule(
                pattern=pattern,
                comment_last_at=comment_last_at,
                ignore_sample_type=ignore_sample_type,
            )
        )
    return rules


def _compute_needtosend_default(row: dict[str, Any]) -> int:
    """기본 needtosend 계산 로직을 적용합니다.

    인자:
        row: Drone SOP 행 dict(행 데이터).

    반환:
        needtosend 값(0/1).

    부작용:
        없음. 순수 계산입니다.
    """

    # -------------------------------------------------------------------------
    # 1) 샘플 타입/코멘트 기준 계산
    # -------------------------------------------------------------------------
    sample_type = str(row.get("sample_type") or "").strip()
    comment = str(row.get("comment") or "").strip()
    last_at = comment.split("@")[-1] if comment else ""
    return _as_int_bool((sample_type != "ENGR_PRODUCTION") and (last_at == "$SETUP_EQP"))


def _compute_needtosend(*, row: dict[str, Any], rules: Sequence[NeedToSendRule]) -> int:
    """룰 기반 needtosend 계산을 수행합니다.

    인자:
        row: Drone SOP 행 dict(행 데이터).
        rules: NeedToSendRule 목록.

    반환:
        needtosend 값(0/1).

    부작용:
        없음. 순수 계산입니다.
    """

    # -------------------------------------------------------------------------
    # 1) 사용자 소속 기반 룰 적용
    # -------------------------------------------------------------------------
    user_sdwt_prod = str(row.get("user_sdwt_prod") or "").strip()
    if user_sdwt_prod and rules:
        for rule in rules:
            if rule.matches(user_sdwt_prod):
                return rule.compute(row)
    # -------------------------------------------------------------------------
    # 2) 기본 로직 fallback
    # -------------------------------------------------------------------------
    return _compute_needtosend_default(row)


def _extract_html_from_email(msg: Any) -> Optional[str]:
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


def _decode_header_value(raw_value: Any) -> str:
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


# =============================================================================
# 메일 제목 필터 상수
# =============================================================================
DEFAULT_DRONE_INCLUDE_SUBJECTS = ("[drone_sop]",)


def _load_include_subjects(raw: Any) -> tuple[str, ...]:
    """환경변수 기반 Drone SOP 메일 제목 포함 목록을 로드합니다.

    인자:
        raw: 제목 목록 문자열(콤마 구분).

    반환:
        소문자화된 제목 튜플.

    부작용:
        없음. 순수 파싱입니다.
    """

    # -------------------------------------------------------------------------
    # 1) 입력 정규화 및 기본값 처리
    # -------------------------------------------------------------------------
    text = str(raw or "").strip()
    if not text:
        return DEFAULT_DRONE_INCLUDE_SUBJECTS

    # -------------------------------------------------------------------------
    # 2) 콤마 구분 문자열 파싱
    # -------------------------------------------------------------------------
    subjects: list[str] = []
    for item in text.split(","):
        cleaned = item.strip().strip("\"'").lower()
        if cleaned:
            subjects.append(cleaned)

    return tuple(subjects) if subjects else DEFAULT_DRONE_INCLUDE_SUBJECTS


def _subject_matches(subject: str, include_subjects: Sequence[str]) -> bool:
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


def _build_drone_sop_row(
    *,
    html: str,
    early_inform_map: dict[tuple[str, str], Optional[str]],
    needtosend_rules: Sequence[NeedToSendRule] | None = None,
) -> Optional[dict[str, Any]]:
    """메일 HTML에서 Drone SOP row를 생성합니다.

    인자:
        html: 메일 HTML 본문.
        early_inform_map: (user_sdwt_prod, main_step) → custom_end_step 매핑.
        needtosend_rules: needtosend 계산 규칙(옵션).

    반환:
        Drone SOP row dict 또는 None.

    부작용:
        없음. 순수 파싱입니다.
    """

    # -------------------------------------------------------------------------
    # 1) <data> 태그 파싱
    # -------------------------------------------------------------------------
    data = _extract_first_data_tag(html)
    if not data:
        return None

    # -------------------------------------------------------------------------
    # 2) 필드 정규화 및 row 구성
    # -------------------------------------------------------------------------
    normalized = {key: _normalize_blank(value) for key, value in data.items()}
    knox_value = normalized.get("knox_id") or normalized.get("knoxid")

    row: dict[str, Any] = {
        "line_id": normalized.get("line_id"),
        "sdwt_prod": normalized.get("sdwt_prod"),
        "sample_type": normalized.get("sample_type"),
        "sample_group": normalized.get("sample_group"),
        "eqp_id": normalized.get("eqp_id"),
        "chamber_ids": (str(normalized.get("chamber_ids") or "").replace(",", "")) or None,
        "lot_id": normalized.get("lot_id"),
        "proc_id": normalized.get("proc_id"),
        "ppid": normalized.get("ppid"),
        "main_step": normalized.get("main_step"),
        "metro_current_step": normalized.get("metro_current_step"),
        "metro_steps": normalized.get("metro_steps"),
        "metro_end_step": normalized.get("metro_end_step"),
        "status": normalized.get("status"),
        "knox_id": knox_value,
        "user_sdwt_prod": normalized.get("user_sdwt_prod"),
        "comment": normalized.get("comment"),
        "defect_url": _sanitize_defect_url(normalized.get("defect_url")),
        "instant_inform": 0,
    }
    # -------------------------------------------------------------------------
    # 3) sop_key 생성
    # -------------------------------------------------------------------------
    row["sop_key"] = build_sop_key(
        line_id=row.get("line_id"),
        eqp_id=row.get("eqp_id"),
        chamber_ids=row.get("chamber_ids"),
        lot_id=row.get("lot_id"),
        main_step=row.get("main_step"),
    )

    # -------------------------------------------------------------------------
    # 4) 조기 알림 기준 custom_end_step 적용
    # -------------------------------------------------------------------------
    user_sdwt_prod = str(row.get("user_sdwt_prod") or "").strip()
    main_step = str(row.get("main_step") or "").strip()
    custom_end_step = early_inform_map.get((user_sdwt_prod, main_step))
    if custom_end_step is not None:
        row["custom_end_step"] = custom_end_step
        current_num = _strip_prefix_num(str(row.get("metro_current_step") or "").strip() or None)
        end_num = _strip_prefix_num(str(custom_end_step).strip() or None)
        if current_num is not None and end_num is not None and current_num >= end_num:
            row["status"] = "COMPLETE"

    # -------------------------------------------------------------------------
    # 5) needtosend 계산
    # -------------------------------------------------------------------------
    row["needtosend"] = _compute_needtosend(row=row, rules=needtosend_rules or ())
    return row


@dataclass(frozen=True)
class DroneSopPop3IngestResult:
    """Drone SOP POP3 수집 실행 결과."""

    matched_mails: int = 0
    upserted_rows: int = 0
    deleted_mails: int = 0
    pruned_rows: int = 0
    skipped: bool = False
    skip_reason: str | None = None


@dataclass(frozen=True)
class DroneSopPop3Config:
    """Drone SOP POP3 수집 설정."""

    host: str
    port: int
    username: str
    password: str
    use_ssl: bool = True
    timeout: int = 60
    include_subjects: tuple[str, ...] = DEFAULT_DRONE_INCLUDE_SUBJECTS
    dummy_mode: bool = False
    dummy_mail_messages_url: str = ""
    needtosend_rules: tuple[NeedToSendRule, ...] = ()

    @classmethod
    def from_settings(cls) -> "DroneSopPop3Config":
        """settings/env에서 POP3 수집 설정을 로드합니다.

        반환:
            DroneSopPop3Config 인스턴스.

        부작용:
            settings/env 값을 조회합니다.
        """

        # ---------------------------------------------------------------------
        # 1) POP3 기본 설정 로드
        # ---------------------------------------------------------------------
        host = (getattr(settings, "DRONE_SOP_POP3_HOST", "") or "").strip()
        port = _parse_int(getattr(settings, "DRONE_SOP_POP3_PORT", None), 995)
        username = (getattr(settings, "DRONE_SOP_POP3_USERNAME", "") or "").strip()
        password = (getattr(settings, "DRONE_SOP_POP3_PASSWORD", "") or "").strip()
        use_ssl = _parse_bool(getattr(settings, "DRONE_SOP_POP3_USE_SSL", None), True)
        timeout = _parse_int(getattr(settings, "DRONE_SOP_POP3_TIMEOUT", None), 60)
        include_subjects_raw = _first_defined(
            (getattr(settings, "DRONE_INCLUDE_SUBJECT_PREFIXES", None) or None),
            (os.getenv("DRONE_INCLUDE_SUBJECT_PREFIXES") or None),
            (getattr(settings, "DRONE_SOP_POP3_SUBJECT_CONTAINS", None) or None),
            (os.getenv("DRONE_SOP_POP3_SUBJECT_CONTAINS") or None),
            "[drone_sop]",
        )
        include_subjects = _load_include_subjects(include_subjects_raw)
        # ---------------------------------------------------------------------
        # 2) 더미 모드/룰 설정 로드
        # ---------------------------------------------------------------------
        dummy_mode = _parse_bool(
            _first_defined(
                getattr(settings, "DRONE_SOP_DUMMY_MODE", None),
                os.getenv("DRONE_SOP_DUMMY_MODE"),
            ),
            False,
        )
        dummy_mail_messages_url = (
            getattr(settings, "DRONE_SOP_DUMMY_MAIL_MESSAGES_URL", "")
            or os.getenv("DRONE_SOP_DUMMY_MAIL_MESSAGES_URL")
            or ""
        ).strip()

        needtosend_rules_raw = getattr(settings, "DRONE_SOP_NEEDTOSEND_RULES", None)
        if needtosend_rules_raw is None:
            needtosend_rules_raw = os.getenv("DRONE_SOP_NEEDTOSEND_RULES")
        needtosend_rules = tuple(_parse_needtosend_rules(needtosend_rules_raw))

        # ---------------------------------------------------------------------
        # 3) 설정 객체 반환
        # ---------------------------------------------------------------------
        return cls(
            host=host,
            port=port,
            username=username,
            password=password,
            use_ssl=use_ssl,
            timeout=timeout,
            include_subjects=include_subjects,
            dummy_mode=dummy_mode,
            dummy_mail_messages_url=dummy_mail_messages_url,
            needtosend_rules=needtosend_rules,
        )


def _list_dummy_mail_messages(*, url: str, timeout: int) -> list[dict[str, Any]]:
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


def _delete_dummy_mail_messages(*, url: str, mail_ids: Sequence[int], timeout: int) -> int:
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


def _upsert_drone_sop_rows(*, rows: Sequence[dict[str, Any]]) -> int:
    """Drone SOP row를 upsert 합니다.

    인자:
        rows: Drone SOP row dict 목록.

    반환:
        처리한 row 개수.

    부작용:
        DB에 INSERT/UPDATE가 발생합니다.
    """

    # -------------------------------------------------------------------------
    # 1) 입력 확인
    # -------------------------------------------------------------------------
    if not rows:
        return 0

    # -------------------------------------------------------------------------
    # 2) SQL 구성
    # -------------------------------------------------------------------------
    insert_cols = [
        "sop_key",
        "line_id",
        "sdwt_prod",
        "sample_type",
        "sample_group",
        "eqp_id",
        "chamber_ids",
        "lot_id",
        "proc_id",
        "ppid",
        "main_step",
        "metro_current_step",
        "metro_steps",
        "metro_end_step",
        "status",
        "knox_id",
        "user_sdwt_prod",
        "comment",
        "defect_url",
        "instant_inform",
        "needtosend",
        "custom_end_step",
    ]
    conflict_cols = ["sop_key"]
    exclude_update_cols = {"needtosend", "comment", "instant_inform", "sop_key"}

    placeholders = ",".join(["%s"] * len(insert_cols))
    quoted_table = f'"{DroneSOP._meta.db_table}"'
    quoted_insert_cols = ", ".join(f'"{col}"' for col in insert_cols)
    conflict_target = ", ".join(f'"{col}"' for col in conflict_cols)

    update_parts = [
        f'"{col}" = COALESCE(EXCLUDED."{col}", {quoted_table}."{col}")'
        for col in insert_cols
        if col not in exclude_update_cols
    ]
    update_clause = ", ".join(update_parts)

    sql = f"""
        INSERT INTO {quoted_table} ({quoted_insert_cols})
        VALUES ({placeholders})
        ON CONFLICT ({conflict_target})
        DO UPDATE SET {update_clause}
    """

    # -------------------------------------------------------------------------
    # 3) 바인드 파라미터 구성
    # -------------------------------------------------------------------------
    args = []
    for row in rows:
        values: list[Any] = []
        if not row.get("sop_key"):
            row["sop_key"] = build_sop_key(
                line_id=row.get("line_id"),
                eqp_id=row.get("eqp_id"),
                chamber_ids=row.get("chamber_ids"),
                lot_id=row.get("lot_id"),
                main_step=row.get("main_step"),
            )
        for col in insert_cols:
            value = row.get(col)
            if value is None and col == "instant_inform":
                value = 0
            values.append(value)
        args.append(tuple(values))
    # -------------------------------------------------------------------------
    # 4) SQL 실행
    # -------------------------------------------------------------------------
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.executemany(sql, args)

    return len(rows)


def _prune_old_drone_sop_rows(*, days: int) -> int:
    """지정 일수보다 오래된 DroneSOP 레코드를 정리합니다.

    인자:
        days: 보관 일수.

    반환:
        삭제된 레코드 수.

    부작용:
        DB 삭제가 발생합니다.
    """

    cutoff = timezone.now() - timedelta(days=days)
    deleted, _ = DroneSOP.objects.filter(created_at__lt=cutoff).delete()
    return int(deleted or 0)


def run_drone_sop_pop3_ingest_from_env() -> DroneSopPop3IngestResult:
    """Drone SOP POP3 수집을 실행합니다.

    반환:
        DroneSopPop3IngestResult 결과 객체.

    부작용:
        - POP3(또는 더미 메일 API)에서 메일을 읽고 삭제합니다.
        - drone_sop 테이블에 upsert 합니다.
        - 90일 초과 데이터는 정리합니다.

    오류:
        설정 누락 또는 POP3 오류 시 예외가 발생할 수 있습니다.
    """

    # -------------------------------------------------------------------------
    # 1) 설정 로드 및 락 획득
    # -------------------------------------------------------------------------
    config = DroneSopPop3Config.from_settings()
    early_inform_map = selectors.load_drone_sop_custom_end_step_map()

    lock_id = _lock_key("drone_sop_pop3_ingest")
    acquired = _try_advisory_lock(lock_id)
    if not acquired:
        return DroneSopPop3IngestResult(skipped=True, skip_reason="already_running")

    try:
        # ---------------------------------------------------------------------
        # 2) 더미 모드 처리(로컬 개발)
        # ---------------------------------------------------------------------
        if config.dummy_mode:
            if not config.dummy_mail_messages_url:
                raise ValueError("DRONE_SOP_DUMMY_MAIL_MESSAGES_URL 미설정")

            matched = 0
            upserted = 0
            delete_targets: list[int] = []
            messages = _list_dummy_mail_messages(url=config.dummy_mail_messages_url, timeout=config.timeout)
            for message in messages:
                subject = _decode_header_value(message.get("subject"))
                if not _subject_matches(subject, config.include_subjects):
                    continue
                body_html = str(message.get("body_html") or message.get("body_text") or "")
                if not body_html:
                    continue
                try:
                    parsed = _build_drone_sop_row(
                        html=body_html,
                        early_inform_map=early_inform_map,
                        needtosend_rules=config.needtosend_rules,
                    )
                except Exception:
                    logger.exception("Failed to parse dummy mail id=%s subject=%r", message.get("id"), subject)
                    continue
                if not parsed:
                    continue
                matched += 1

                try:
                    upserted += _upsert_drone_sop_rows(rows=[parsed])
                except Exception:
                    logger.exception("Failed to upsert dummy mail id=%s subject=%r", message.get("id"), subject)
                    continue

                try:
                    delete_targets.append(int(message.get("id")))
                except (TypeError, ValueError):
                    continue

            if matched == 0:
                return DroneSopPop3IngestResult(
                    matched_mails=matched,
                    upserted_rows=0,
                    deleted_mails=0,
                    pruned_rows=0,
                )

            pruned = 0
            try:
                pruned = _prune_old_drone_sop_rows(days=90)
            except Exception:
                logger.exception("Failed to prune old DroneSOP rows")

            deleted = 0
            if delete_targets:
                deleted = _delete_dummy_mail_messages(
                    url=config.dummy_mail_messages_url,
                    mail_ids=delete_targets,
                    timeout=config.timeout,
                )

            return DroneSopPop3IngestResult(
                matched_mails=matched,
                upserted_rows=upserted,
                deleted_mails=deleted,
                pruned_rows=pruned,
            )

        # ---------------------------------------------------------------------
        # 3) POP3 수집 처리
        # ---------------------------------------------------------------------
        if not config.host or not config.username or not config.password:
            raise ValueError("POP3 connection info is incomplete (host/username/password required)")

        client_cls = poplib.POP3_SSL if config.use_ssl else poplib.POP3
        client = client_cls(config.host, config.port, timeout=config.timeout)
        matched = 0
        upserted = 0
        deleted = 0

        try:
            client.user(config.username)
            client.pass_(config.password)
            num_msgs = len(client.list()[1])
            for msg_num in range(1, num_msgs + 1):
                _, lines, _ = client.retr(msg_num)
                msg = BytesParser(policy=default).parsebytes(b"\r\n".join(lines))
                subject = _decode_header_value(msg.get("Subject"))
                if not _subject_matches(subject, config.include_subjects):
                    continue
                html = _extract_html_from_email(msg)
                if not html:
                    continue
                try:
                    parsed = _build_drone_sop_row(
                        html=html,
                        early_inform_map=early_inform_map,
                        needtosend_rules=config.needtosend_rules,
                    )
                except Exception:
                    logger.exception("Failed to parse POP3 message #%s subject=%r", msg_num, subject)
                    continue
                if not parsed:
                    continue
                matched += 1
                try:
                    upserted += _upsert_drone_sop_rows(rows=[parsed])
                except Exception:
                    logger.exception("Failed to upsert POP3 message #%s subject=%r", msg_num, subject)
                    continue
                try:
                    client.dele(msg_num)
                    deleted += 1
                except Exception:
                    logger.exception("Failed to mark POP3 message #%s for deletion", msg_num)

            pruned = 0
            try:
                if upserted:
                    pruned = _prune_old_drone_sop_rows(days=90)
            except Exception:
                logger.exception("Failed to prune old DroneSOP rows")

            client.quit()
            return DroneSopPop3IngestResult(
                matched_mails=matched,
                upserted_rows=upserted,
                deleted_mails=deleted,
                pruned_rows=pruned,
            )
        except Exception:
            logger.exception("Drone SOP POP3 ingest failed; rolling back POP3 deletions via rset()")
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
    finally:
        # ---------------------------------------------------------------------
        # 4) advisory lock 해제
        # ---------------------------------------------------------------------
        if acquired:
            _release_advisory_lock(lock_id)
