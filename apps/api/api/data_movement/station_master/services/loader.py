"""station_master 파일 적재 서비스입니다."""

from __future__ import annotations

import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from django.db import transaction
from django.utils import timezone

from api.data_movement.common.services.deflate_csv import read_deflate_csv_file
from api.data_movement.common.services.file_loader import (
    ClaimedDataFile,
    claim_incoming_file,
    delete_claimed_file,
    list_incoming_files,
)
from api.data_movement.common.services.postgres_copy import copy_full_replace_rows
from api.data_movement.station_master.models import StationMasterLoadJob
from api.data_movement.station_master.services import spec


RAW_PREVIEW_LINE_LIMIT = 5
RAW_PREVIEW_CHAR_LIMIT = 500


@dataclass(frozen=True)
class LoadFileOutcome:
    """단일 파일 처리 결과입니다."""

    file_name: str
    status: str
    row_count: int
    replace_scope: str = spec.REPLACE_SCOPE
    error_message: str | None = None
    raw_diagnostic: dict[str, Any] | None = None


@dataclass(frozen=True)
class LoadRunSummary:
    """station_master 적재 실행 요약입니다."""

    outcomes: list[LoadFileOutcome]

    @property
    def processed_count(self) -> int:
        """처리한 파일 수를 반환합니다."""

        return len(self.outcomes)

    @property
    def success_count(self) -> int:
        """성공한 파일 수를 반환합니다."""

        return sum(1 for outcome in self.outcomes if outcome.status == StationMasterLoadJob.Status.SUCCESS)

    @property
    def failure_count(self) -> int:
        """실패한 파일 수를 반환합니다."""

        return sum(1 for outcome in self.outcomes if outcome.status == StationMasterLoadJob.Status.FAILED)


@dataclass(frozen=True)
class RawStationFileDiagnostic:
    """원본 station_master 파일의 구분자와 컬럼 개수를 진단합니다."""

    expected_column_count: int
    separator: str
    row_count: int
    bad_row_count: int
    sample_row_column_counts: list[dict[str, int]]
    first_bad_rows: list[dict[str, int]]
    raw_preview_lines: list[dict[str, Any]]
    delimiter_mismatch_suspected: bool

    def to_dict(self) -> dict[str, Any]:
        """API 응답과 command 출력에 사용할 dict로 변환합니다."""

        return {
            "expected_column_count": self.expected_column_count,
            "separator": self.separator,
            "row_count": self.row_count,
            "bad_row_count": self.bad_row_count,
            "sample_row_column_counts": self.sample_row_column_counts,
            "first_bad_rows": self.first_bad_rows,
            "raw_preview_lines": self.raw_preview_lines,
            "delimiter_mismatch_suspected": self.delimiter_mismatch_suspected,
        }

    def summary_message(self) -> str:
        """진단 결과를 한 줄 메시지로 요약합니다."""

        message = (
            "raw diagnostic: "
            f"expected_columns={self.expected_column_count}, "
            f"separator={self.separator!r}, rows={self.row_count}, "
            f"bad_rows={self.bad_row_count}"
        )
        if self.delimiter_mismatch_suspected:
            message = f"{message}, delimiter_mismatch_suspected=True"
        if self.first_bad_rows:
            message = f"{message}, first_bad_rows={self.first_bad_rows}"
        return message


def _finish_job(
    *,
    job: StationMasterLoadJob,
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


def _create_job(*, claimed_file: ClaimedDataFile) -> StationMasterLoadJob:
    """선점한 파일 기준으로 적재 이력 row를 생성합니다."""

    return StationMasterLoadJob.objects.create(
        file_name=claimed_file.original_name,
        file_path=str(claimed_file.original_path),
        status=StationMasterLoadJob.Status.RUNNING,
        started_at=timezone.now(),
    )


def _diagnose_raw_station_file(*, file_path: Path) -> RawStationFileDiagnostic:
    """deflate 해제 후 원본 row의 구분자와 컬럼 개수를 확인합니다."""

    try:
        raw = zlib.decompress(file_path.read_bytes()).decode("utf-8", "replace")
    except zlib.error as exc:
        raise ValueError(f"deflate 압축 해제 실패: {file_path}") from exc

    expected_column_count = len(spec.COLUMNS)
    lines = raw.splitlines()
    sample_row_column_counts: list[dict[str, int]] = []
    first_bad_rows: list[dict[str, int]] = []
    raw_preview_lines: list[dict[str, Any]] = []
    row_counts: list[int] = []
    for row_number, line in enumerate(lines, start=1):
        column_count = len(line.split(spec.FILE_SEPARATOR))
        row_counts.append(column_count)
        if row_number <= RAW_PREVIEW_LINE_LIMIT:
            sample_row_column_counts.append({"row": row_number, "column_count": column_count})
            raw_preview_lines.append(
                {
                    "row": row_number,
                    "preview": line[:RAW_PREVIEW_CHAR_LIMIT],
                    "truncated": len(line) > RAW_PREVIEW_CHAR_LIMIT,
                }
            )
        if column_count != expected_column_count and len(first_bad_rows) < 20:
            first_bad_rows.append({"row": row_number, "column_count": column_count})

    delimiter_mismatch_suspected = bool(lines) and all(column_count == 1 for column_count in row_counts)
    return RawStationFileDiagnostic(
        expected_column_count=expected_column_count,
        separator=spec.FILE_SEPARATOR,
        row_count=len(lines),
        bad_row_count=sum(1 for column_count in row_counts if column_count != expected_column_count),
        sample_row_column_counts=sample_row_column_counts,
        first_bad_rows=first_bad_rows,
        raw_preview_lines=raw_preview_lines,
        delimiter_mismatch_suspected=delimiter_mismatch_suspected,
    )


def _read_station_frame(*, file_path: Path):
    """station_master deflate CSV를 spec 기준 DataFrame으로 읽습니다."""

    return read_deflate_csv_file(
        file_path=file_path,
        columns=spec.COLUMNS,
        datetime_columns=spec.DATETIME_COLUMNS,
        float_columns=spec.FLOAT_COLUMNS,
        separator=spec.FILE_SEPARATOR,
    )


def _load_claimed_file(*, claimed_file: ClaimedDataFile) -> LoadFileOutcome:
    """processing으로 선점한 station 파일을 대상 테이블에 전체 반영합니다."""

    job = _create_job(claimed_file=claimed_file)

    try:
        frame = _read_station_frame(file_path=claimed_file.working_path)
        row_count = frame.shape[0]
        if row_count == 0:
            raise ValueError(f"empty dataframe: {claimed_file.original_path}")

        with transaction.atomic():
            result = copy_full_replace_rows(
                frame=frame,
                table_name=spec.TABLE_NAME,
                columns=spec.COLUMNS,
                temp_table_name=spec.TEMP_TABLE_NAME,
            )

        delete_claimed_file(claimed_file=claimed_file)

        _finish_job(
            job=job,
            status=StationMasterLoadJob.Status.SUCCESS,
            row_count=result.row_count,
        )
        return LoadFileOutcome(
            file_name=claimed_file.original_name,
            status=StationMasterLoadJob.Status.SUCCESS,
            row_count=result.row_count,
        )
    except Exception as exc:
        error_message = str(exc)
        delete_claimed_file(claimed_file=claimed_file)
        _finish_job(
            job=job,
            status=StationMasterLoadJob.Status.FAILED,
            row_count=0,
            error_message=error_message,
        )
        return LoadFileOutcome(
            file_name=claimed_file.original_name,
            status=StationMasterLoadJob.Status.FAILED,
            row_count=0,
            error_message=error_message,
        )


def _dry_run_one_file(*, file_path: Path) -> LoadFileOutcome:
    """파일 이동 없이 단일 station 파일을 파싱 검증합니다."""

    job = StationMasterLoadJob.objects.create(
        file_name=file_path.name,
        file_path=str(file_path),
        status=StationMasterLoadJob.Status.RUNNING,
        started_at=timezone.now(),
    )

    diagnostic: RawStationFileDiagnostic | None = None
    try:
        diagnostic = _diagnose_raw_station_file(file_path=file_path)
        if diagnostic.bad_row_count:
            raise ValueError(diagnostic.summary_message())

        frame = _read_station_frame(file_path=file_path)
        row_count = frame.shape[0]
        if row_count == 0:
            raise ValueError(f"empty dataframe: {file_path}")

        _finish_job(
            job=job,
            status=StationMasterLoadJob.Status.DRY_RUN,
            row_count=row_count,
        )
        return LoadFileOutcome(
            file_name=file_path.name,
            status=StationMasterLoadJob.Status.DRY_RUN,
            row_count=row_count,
            raw_diagnostic=diagnostic.to_dict(),
        )
    except Exception as exc:
        error_message = str(exc)
        _finish_job(
            job=job,
            status=StationMasterLoadJob.Status.FAILED,
            row_count=0,
            error_message=error_message,
        )
        return LoadFileOutcome(
            file_name=file_path.name,
            status=StationMasterLoadJob.Status.FAILED,
            row_count=0,
            error_message=error_message,
            raw_diagnostic=diagnostic.to_dict() if diagnostic is not None else None,
        )


def _load_one_file(*, file_path: Path, table_dir: Path, dry_run: bool) -> LoadFileOutcome:
    """단일 station 파일을 읽고 대상 테이블에 전체 반영합니다."""

    if dry_run:
        return _dry_run_one_file(file_path=file_path)

    claimed_file = claim_incoming_file(file_path=file_path, table_dir=table_dir)
    return _load_claimed_file(claimed_file=claimed_file)


def load_station_master_files(
    *,
    data_dir: Path | str | None = None,
    dry_run: bool = False,
    limit: int | None = None,
) -> LoadRunSummary:
    """station_master deflate CSV 파일들을 순차 적재합니다."""

    resolved_table_dir = Path(data_dir) if data_dir is not None else spec.DEFAULT_TABLE_DIR
    files = list_incoming_files(table_dir=resolved_table_dir, pattern=spec.FILE_PATTERN, limit=limit)

    outcomes = [
        _load_one_file(file_path=file_path, table_dir=resolved_table_dir, dry_run=dry_run)
        for file_path in files
    ]
    return LoadRunSummary(outcomes=outcomes)
