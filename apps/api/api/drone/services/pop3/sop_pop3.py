# =============================================================================
# 모듈: Drone SOP POP3 수집 서비스
# 주요 기능: POP3/더미 메일 수집, SOP upsert, 정리 작업
# 주요 가정: 오프라인 개발은 더미 메일 API로 대체합니다.
# =============================================================================
"""Drone SOP POP3 수집 헬퍼 모듈입니다."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Optional, Sequence

from django.db import connection, transaction
from django.utils import timezone

from ... import selectors
from ...models import DroneSOP, build_sop_key
from ..shared.delivery_state import ensure_channel_delivery_snapshots_for_rows
from ..shared.notify_resolver import (
    UserSdwtProdMapIndex,
    load_user_sdwt_prod_map_index,
    resolve_target_user_sdwt_prods,
)
from ..shared.utils import _advisory_lock
from .config import (
    DroneSopPop3Config,
    DroneSopPop3IngestResult,
    NeedToSendRule,
)
from .defectmap_sidecar import post_defect_png_sidecar_if_needed
from .dummy_mail import (
    delete_dummy_mail_messages as _delete_dummy_mail_messages,
    list_dummy_mail_messages as _list_dummy_mail_messages,
)
from .mailbox import (
    authenticate_pop3_client as _authenticate_pop3_client,
    close_pop3_client as _close_pop3_client,
    create_pop3_client as _create_pop3_client,
    decode_header_value as _decode_header_value,
    extract_html_from_email as _extract_html_from_email,
    list_pop3_message_numbers as _list_pop3_message_numbers,
    mark_pop3_message_for_deletion as _mark_pop3_message_for_deletion,
    retrieve_pop3_message as _retrieve_pop3_message,
    rollback_pop3_deletions as _rollback_pop3_deletions,
    subject_matches as _subject_matches,
)
from .row_builder import build_drone_sop_row as _build_drone_sop_row

logger = logging.getLogger(__name__)


def build_drone_sop_row(
    *,
    html: str,
    early_inform_map: dict[tuple[str, str], Optional[str]],
    user_sdwt_map_index: UserSdwtProdMapIndex | None = None,
    needtosend_rule_cache: dict[str, NeedToSendRule | None] | None = None,
) -> Optional[dict[str, Any]]:
    """메일 HTML에서 Drone SOP row를 생성하는 공개 함수입니다."""

    return _build_drone_sop_row(
        html=html,
        early_inform_map=early_inform_map,
        user_sdwt_map_index=user_sdwt_map_index,
        needtosend_rule_cache=needtosend_rule_cache,
    )


def _ensure_snapshots_for_upserted_rows(*, source_by_sop_key: dict[str, dict[str, Any]]) -> None:
    """upsert 완료된 SOP에 delivery snapshot을 생성합니다."""

    if not source_by_sop_key:
        return

    db_rows = DroneSOP.objects.filter(sop_key__in=list(source_by_sop_key.keys())).values(
        "id",
        "sop_key",
        "sdwt_prod",
        "user_sdwt_prod",
        "status",
        "needtosend",
        "instant_inform",
    )
    snapshot_rows: list[dict[str, Any]] = []
    for db_row in db_rows:
        sop_key = str(db_row.get("sop_key") or "").strip()
        source_row = source_by_sop_key.get(sop_key) or {}
        snapshot_row = dict(db_row)
        if isinstance(source_row.get("target_user_sdwt_prods"), list):
            snapshot_row["target_user_sdwt_prods"] = source_row["target_user_sdwt_prods"]
        elif source_row.get("target_user_sdwt_prod") is not None:
            snapshot_row["target_user_sdwt_prod"] = source_row.get("target_user_sdwt_prod")
        snapshot_rows.append(snapshot_row)

    ensure_channel_delivery_snapshots_for_rows(rows=snapshot_rows)


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

    update_parts: list[str] = []
    for col in insert_cols:
        if col in exclude_update_cols:
            continue
        if col == "defect_url":
            update_parts.append(f'"{col}" = EXCLUDED."{col}"')
            continue
        update_parts.append(
            f'"{col}" = COALESCE(EXCLUDED."{col}", {quoted_table}."{col}")'
        )
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
    source_by_sop_key: dict[str, dict[str, Any]] = {}
    user_sdwt_map_index: UserSdwtProdMapIndex | None = None
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
        if not row.get("target_user_sdwt_prod"):
            if user_sdwt_map_index is None:
                user_sdwt_map_index = load_user_sdwt_prod_map_index()
            target_user_sdwt_prods = resolve_target_user_sdwt_prods(row=row, index=user_sdwt_map_index)
            target_user_sdwt_prod = target_user_sdwt_prods[0] if target_user_sdwt_prods else None
            row["target_user_sdwt_prods"] = target_user_sdwt_prods
            row["target_user_sdwt_prod"] = target_user_sdwt_prod
        sop_key = str(row.get("sop_key") or "").strip()
        if sop_key:
            source_by_sop_key[sop_key] = dict(row)
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
        _ensure_snapshots_for_upserted_rows(source_by_sop_key=source_by_sop_key)

    return len(rows)


def upsert_drone_sop_rows(*, rows: Sequence[dict[str, Any]]) -> int:
    """Drone SOP row를 upsert 하는 공개 함수입니다."""

    return _upsert_drone_sop_rows(rows=rows)


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


def _safe_prune_rows(*, days: int, only_when_upserted: bool, upserted_rows: int) -> int:
    """오래된 DroneSOP 행 정리를 안전하게 수행합니다."""

    if only_when_upserted and upserted_rows <= 0:
        return 0
    try:
        return _prune_old_drone_sop_rows(days=days)
    except Exception:
        logger.exception("Failed to prune old DroneSOP rows")
        return 0


def _parse_drone_sop_row_or_none(
    *,
    html: str,
    early_inform_map: dict[tuple[str, str], Optional[str]],
    user_sdwt_map_index: UserSdwtProdMapIndex,
    needtosend_rule_cache: dict[str, NeedToSendRule | None],
    error_label: str,
) -> Optional[dict[str, Any]]:
    """HTML 본문을 Drone SOP row로 파싱합니다."""

    try:
        return _build_drone_sop_row(
            html=html,
            early_inform_map=early_inform_map,
            user_sdwt_map_index=user_sdwt_map_index,
            needtosend_rule_cache=needtosend_rule_cache,
        )
    except Exception:
        logger.exception("Failed to parse %s", error_label)
        return None


def _upsert_drone_sop_row_or_zero(*, row: dict[str, Any], error_label: str) -> int:
    """Drone SOP row upsert를 수행하고 실패 시 0을 반환합니다."""

    try:
        return _upsert_drone_sop_rows(rows=[row])
    except Exception:
        logger.exception("Failed to upsert %s", error_label)
        return 0


def _run_dummy_mode_ingest(
    *,
    config: DroneSopPop3Config,
    early_inform_map: dict[tuple[str, str], Optional[str]],
    user_sdwt_map_index: UserSdwtProdMapIndex,
    needtosend_rule_cache: dict[str, NeedToSendRule | None],
) -> DroneSopPop3IngestResult:
    """더미 메일 API 기반 수집을 실행합니다."""

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

        parsed = _parse_drone_sop_row_or_none(
            html=body_html,
            early_inform_map=early_inform_map,
            user_sdwt_map_index=user_sdwt_map_index,
            needtosend_rule_cache=needtosend_rule_cache,
            error_label=f"dummy mail id={message.get('id')} subject={subject!r}",
        )
        if not parsed:
            continue

        # 임시 부가기능: defectmap 전송(실패해도 메인 수집 흐름은 계속 진행합니다).
        post_defect_png_sidecar_if_needed(
            row=parsed,
            config=config,
            scanned_at=timezone.now(),
            error_label=f"dummy mail id={message.get('id')} subject={subject!r}",
        )
        matched += 1
        upserted_count = _upsert_drone_sop_row_or_zero(
            row=parsed,
            error_label=f"dummy mail id={message.get('id')} subject={subject!r}",
        )
        upserted += upserted_count
        if upserted_count <= 0:
            continue

        try:
            delete_targets.append(int(message.get("id")))
        except (TypeError, ValueError):
            continue

    if matched == 0:
        return DroneSopPop3IngestResult(
            matched_mails=0,
            upserted_rows=0,
            deleted_mails=0,
            pruned_rows=0,
        )

    pruned = _safe_prune_rows(days=90, only_when_upserted=False, upserted_rows=upserted)
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


def _run_pop3_mode_ingest(
    *,
    config: DroneSopPop3Config,
    early_inform_map: dict[tuple[str, str], Optional[str]],
    user_sdwt_map_index: UserSdwtProdMapIndex,
    needtosend_rule_cache: dict[str, NeedToSendRule | None],
) -> DroneSopPop3IngestResult:
    """실 POP3 기반 수집을 실행합니다."""

    client = _create_pop3_client(config=config)
    matched = 0
    upserted = 0
    deleted = 0

    try:
        _authenticate_pop3_client(client=client, config=config)
        for msg_num in _list_pop3_message_numbers(client=client):
            msg = _retrieve_pop3_message(client=client, msg_num=msg_num)
            subject = _decode_header_value(msg.get("Subject"))
            if not _subject_matches(subject, config.include_subjects):
                continue

            html = _extract_html_from_email(msg)
            if not html:
                continue

            parsed = _parse_drone_sop_row_or_none(
                html=html,
                early_inform_map=early_inform_map,
                user_sdwt_map_index=user_sdwt_map_index,
                needtosend_rule_cache=needtosend_rule_cache,
                error_label=f"POP3 message #{msg_num} subject={subject!r}",
            )
            if not parsed:
                continue

            # 임시 부가기능: defectmap 전송(실패해도 메인 수집 흐름은 계속 진행합니다).
            post_defect_png_sidecar_if_needed(
                row=parsed,
                config=config,
                scanned_at=timezone.now(),
                error_label=f"POP3 message #{msg_num} subject={subject!r}",
            )
            matched += 1
            upserted_count = _upsert_drone_sop_row_or_zero(
                row=parsed,
                error_label=f"POP3 message #{msg_num} subject={subject!r}",
            )
            upserted += upserted_count
            if upserted_count <= 0:
                continue

            try:
                _mark_pop3_message_for_deletion(client=client, msg_num=msg_num)
                deleted += 1
            except Exception:
                logger.exception("Failed to mark POP3 message #%s for deletion", msg_num)

        pruned = _safe_prune_rows(days=90, only_when_upserted=True, upserted_rows=upserted)
        return DroneSopPop3IngestResult(
            matched_mails=matched,
            upserted_rows=upserted,
            deleted_mails=deleted,
            pruned_rows=pruned,
        )
    except Exception:
        logger.exception("Drone SOP POP3 ingest failed; rolling back POP3 deletions via rset()")
        try:
            _rollback_pop3_deletions(client=client)
        except Exception:
            logger.debug("POP3 rset failed")
        raise
    finally:
        try:
            _close_pop3_client(client=client)
        except Exception:
            pass


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
    # 1) 설정/캐시 준비
    # -------------------------------------------------------------------------
    config = DroneSopPop3Config.from_settings()
    early_inform_map = selectors.load_drone_sop_custom_end_step_map()
    user_sdwt_map_index = load_user_sdwt_prod_map_index()
    needtosend_rule_cache: dict[str, NeedToSendRule | None] = {}

    # -------------------------------------------------------------------------
    # 2) 락 획득 후 모드별 실행
    # -------------------------------------------------------------------------
    with _advisory_lock("drone_sop_pop3_ingest") as acquired:
        if not acquired:
            return DroneSopPop3IngestResult(skipped=True, skip_reason="already_running")

        if config.dummy_mode:
            return _run_dummy_mode_ingest(
                config=config,
                early_inform_map=early_inform_map,
                user_sdwt_map_index=user_sdwt_map_index,
                needtosend_rule_cache=needtosend_rule_cache,
            )
        return _run_pop3_mode_ingest(
            config=config,
            early_inform_map=early_inform_map,
            user_sdwt_map_index=user_sdwt_map_index,
            needtosend_rule_cache=needtosend_rule_cache,
        )


__all__ = [
    "build_drone_sop_row",
    "run_drone_sop_pop3_ingest_from_env",
    "upsert_drone_sop_rows",
]
