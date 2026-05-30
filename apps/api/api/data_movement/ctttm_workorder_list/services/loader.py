"""ctttm_workorder_list 파일 적재 서비스입니다."""

from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from django.db import connection, transaction
from django.utils import timezone

from api.data_movement.common.services.file_loader import (
    ClaimedDataFile,
    claim_incoming_file,
    delete_claimed_file,
    list_incoming_files,
)
from api.data_movement.common.services.streaming_csv import write_selected_deflate_csv
from api.data_movement.ctttm_workorder_list.models import CtttmWorkorderListLoadJob
from api.data_movement.ctttm_workorder_list.services import spec


@dataclass(frozen=True)
class SourceFileInfo:
    """파일명에서 추출한 source 정보입니다."""

    source_type: str
    file_timestamp: str


@dataclass(frozen=True)
class LoadFileOutcome:
    """단일 파일 처리 결과입니다."""

    file_name: str
    status: str
    row_count: int
    source_type: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class LoadRunSummary:
    """ctttm_workorder_list 적재 실행 요약입니다."""

    outcomes: list[LoadFileOutcome]

    @property
    def processed_count(self) -> int:
        """처리한 파일 수를 반환합니다."""

        return len(self.outcomes)

    @property
    def success_count(self) -> int:
        """성공한 파일 수를 반환합니다."""

        return sum(1 for outcome in self.outcomes if outcome.status == CtttmWorkorderListLoadJob.Status.SUCCESS)

    @property
    def failure_count(self) -> int:
        """실패한 파일 수를 반환합니다."""

        return sum(1 for outcome in self.outcomes if outcome.status == CtttmWorkorderListLoadJob.Status.FAILED)


def parse_source_file_name(*, file_name: str) -> SourceFileInfo:
    """파일명에서 source_type과 파일 timestamp를 추출합니다."""

    match = re.match(spec.SOURCE_FILE_PATTERN, file_name)
    if not match:
        raise ValueError(f"지원하지 않는 파일명입니다: {file_name}")
    return SourceFileInfo(
        source_type=match.group("source"),
        file_timestamp=match.group("file_timestamp"),
    )


def _finish_job(
    *,
    job: CtttmWorkorderListLoadJob,
    status: str,
    row_count: int,
    error_message: str | None = None,
) -> None:
    """적재 이력 row를 최종 상태로 갱신합니다."""

    job.status = status
    job.row_count = row_count
    job.error_message = error_message
    job.finished_at = timezone.now()
    job.save(update_fields=["status", "row_count", "error_message", "finished_at"])


def _create_job(*, claimed_file: ClaimedDataFile, source_info: SourceFileInfo | None) -> CtttmWorkorderListLoadJob:
    """선점한 파일 기준으로 적재 이력 row를 생성합니다."""

    return CtttmWorkorderListLoadJob.objects.create(
        file_name=claimed_file.original_name,
        file_path=str(claimed_file.original_path),
        source_type=source_info.source_type if source_info else None,
        file_timestamp=source_info.file_timestamp if source_info else None,
        status=CtttmWorkorderListLoadJob.Status.RUNNING,
        started_at=timezone.now(),
    )


def _create_dry_run_job(*, file_path: Path, source_info: SourceFileInfo | None) -> CtttmWorkorderListLoadJob:
    """dry-run 파일 기준으로 적재 이력 row를 생성합니다."""

    return CtttmWorkorderListLoadJob.objects.create(
        file_name=file_path.name,
        file_path=str(file_path),
        source_type=source_info.source_type if source_info else None,
        file_timestamp=source_info.file_timestamp if source_info else None,
        status=CtttmWorkorderListLoadJob.Status.RUNNING,
        started_at=timezone.now(),
    )


def _quote_identifier(identifier: str) -> str:
    """SQL identifier를 quote 처리합니다."""

    return connection.ops.quote_name(identifier)


def _copy_selected_file_to_temp(*, cursor, selected_csv_path: Path) -> None:
    """선택 컬럼 CSV 파일을 temp table로 COPY 합니다."""

    quoted_temp = _quote_identifier(spec.TEMP_TABLE_NAME)
    quoted_columns = ", ".join(_quote_identifier(column) for column in spec.DB_COLUMNS)
    copy_sql = f"""
        COPY {quoted_temp} ({quoted_columns})
        FROM STDIN
        WITH (
            FORMAT CSV,
            NULL '',
            QUOTE '"',
            ESCAPE '"'
        )
    """
    copy_cursor = getattr(cursor, "cursor", cursor)
    if not hasattr(copy_cursor, "copy"):
        raise RuntimeError("psycopg3 COPY API를 사용할 수 없습니다.")

    with copy_cursor.copy(copy_sql) as copy:
        with selected_csv_path.open("r", encoding="utf-8") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                copy.write(chunk)


def _replace_source_rows(*, selected_csv_path: Path, source_type: str) -> None:
    """source_type 단위로 기존 데이터를 삭제하고 선택 컬럼 CSV를 적재합니다."""

    quoted_table = _quote_identifier(spec.TABLE_NAME)
    quoted_temp = _quote_identifier(spec.TEMP_TABLE_NAME)
    temp_columns_sql = ", ".join(f"{_quote_identifier(column)} text" for column in spec.DB_COLUMNS)

    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                CREATE TEMP TABLE {quoted_temp}
                ({temp_columns_sql})
                ON COMMIT DROP
                """
            )
            _copy_selected_file_to_temp(cursor=cursor, selected_csv_path=selected_csv_path)
            cursor.execute(
                f"DELETE FROM {quoted_table} WHERE {_quote_identifier(spec.REPLACE_COLUMN)} = %s",
                [source_type],
            )
            cursor.execute(
                f"""
                INSERT INTO {quoted_table}
                    (
                        source_type,
                        workorder_id,
                        line_id,
                        eqp_id,
                        work_type,
                        description,
                        inprg_date,
                        comp_date
                    )
                SELECT
                    %s,
                    NULLIF(workorder_id, ''),
                    NULLIF(line_id, ''),
                    NULLIF(eqp_id, ''),
                    NULLIF(work_type, ''),
                    NULLIF(description, ''),
                    NULLIF(inprg_date, '')::timestamp,
                    NULLIF(comp_date, '')::timestamp
                FROM {quoted_temp}
                """,
                [source_type],
            )


def _write_selected_csv(*, source_path: Path, output_dir: Path) -> tuple[Path, int]:
    """원본 deflate CSV에서 저장 대상 컬럼만 추출한 임시 CSV를 생성합니다."""

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".selected.csv",
        dir=output_dir,
        delete=False,
    ) as handle:
        selected_path = Path(handle.name)

    try:
        row_count = write_selected_deflate_csv(
            source_path=source_path,
            output_path=selected_path,
            file_columns=spec.FILE_COLUMNS,
            db_columns=spec.DB_COLUMNS,
            column_sources=spec.COLUMN_SOURCES,
            row_filters=spec.ROW_FILTERS,
            min_datetime_filters={
                spec.CREATE_DATE_FILTER_COLUMN: _create_date_cutoff(),
            },
        )
    except Exception:
        selected_path.unlink(missing_ok=True)
        raise

    return selected_path, row_count


def _create_date_cutoff() -> datetime:
    """CREATE_DATE 필터에 사용할 180일 전 기준 시각을 반환합니다."""

    return timezone.localtime(timezone.now()).replace(tzinfo=None) - timedelta(days=spec.CREATE_DATE_LOOKBACK_DAYS)


def _load_claimed_file(*, claimed_file: ClaimedDataFile) -> LoadFileOutcome:
    """processing으로 선점한 workorder 파일을 source_type 단위로 반영합니다."""

    source_info: SourceFileInfo | None = None
    job: CtttmWorkorderListLoadJob | None = None
    selected_path: Path | None = None

    try:
        source_info = parse_source_file_name(file_name=claimed_file.original_name)
        job = _create_job(claimed_file=claimed_file, source_info=source_info)
        selected_path, row_count = _write_selected_csv(
            source_path=claimed_file.working_path,
            output_dir=claimed_file.working_path.parent,
        )
        if row_count == 0:
            raise ValueError(f"empty dataframe: {claimed_file.original_path}")

        _replace_source_rows(selected_csv_path=selected_path, source_type=source_info.source_type)

        _finish_job(
            job=job,
            status=CtttmWorkorderListLoadJob.Status.SUCCESS,
            row_count=row_count,
        )
        return LoadFileOutcome(
            file_name=claimed_file.original_name,
            status=CtttmWorkorderListLoadJob.Status.SUCCESS,
            row_count=row_count,
            source_type=source_info.source_type,
        )
    except Exception as exc:
        error_message = str(exc)
        if job is None:
            job = _create_job(claimed_file=claimed_file, source_info=source_info)
        _finish_job(
            job=job,
            status=CtttmWorkorderListLoadJob.Status.FAILED,
            row_count=0,
            error_message=error_message,
        )
        return LoadFileOutcome(
            file_name=claimed_file.original_name,
            status=CtttmWorkorderListLoadJob.Status.FAILED,
            row_count=0,
            source_type=source_info.source_type if source_info else None,
            error_message=error_message,
        )
    finally:
        if selected_path is not None:
            selected_path.unlink(missing_ok=True)
        delete_claimed_file(claimed_file=claimed_file)


def _dry_run_one_file(*, file_path: Path) -> LoadFileOutcome:
    """파일 이동 없이 단일 workorder 파일을 파싱 검증합니다."""

    source_info: SourceFileInfo | None = None
    selected_path: Path | None = None
    job: CtttmWorkorderListLoadJob | None = None
    try:
        source_info = parse_source_file_name(file_name=file_path.name)
        job = _create_dry_run_job(file_path=file_path, source_info=source_info)
        with tempfile.TemporaryDirectory() as temp_dir:
            selected_path, row_count = _write_selected_csv(
                source_path=file_path,
                output_dir=Path(temp_dir),
            )
            if row_count == 0:
                raise ValueError(f"empty dataframe: {file_path}")
        _finish_job(
            job=job,
            status=CtttmWorkorderListLoadJob.Status.DRY_RUN,
            row_count=row_count,
        )
        return LoadFileOutcome(
            file_name=file_path.name,
            status=CtttmWorkorderListLoadJob.Status.DRY_RUN,
            row_count=row_count,
            source_type=source_info.source_type,
        )
    except Exception as exc:
        error_message = str(exc)
        if job is None:
            job = _create_dry_run_job(file_path=file_path, source_info=source_info)
        _finish_job(
            job=job,
            status=CtttmWorkorderListLoadJob.Status.FAILED,
            row_count=0,
            error_message=error_message,
        )
        return LoadFileOutcome(
            file_name=file_path.name,
            status=CtttmWorkorderListLoadJob.Status.FAILED,
            row_count=0,
            source_type=source_info.source_type if source_info else None,
            error_message=error_message,
        )
    finally:
        if selected_path is not None:
            selected_path.unlink(missing_ok=True)


def load_ctttm_workorder_list_files(
    *,
    data_dir: Path | str | None = None,
    dry_run: bool = False,
    limit: int | None = None,
) -> LoadRunSummary:
    """ctttm_workorder_list deflate CSV 파일들을 순차 적재합니다."""

    resolved_table_dir = Path(data_dir) if data_dir is not None else spec.DEFAULT_TABLE_DIR
    files = list_incoming_files(table_dir=resolved_table_dir, pattern=spec.FILE_PATTERN, limit=limit)
    outcomes = []
    for file_path in files:
        if dry_run:
            outcomes.append(_dry_run_one_file(file_path=file_path))
            continue
        claimed_file = claim_incoming_file(file_path=file_path, table_dir=resolved_table_dir)
        outcomes.append(_load_claimed_file(claimed_file=claimed_file))
    return LoadRunSummary(outcomes=outcomes)
