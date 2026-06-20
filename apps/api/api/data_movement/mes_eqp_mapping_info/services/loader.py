"""mes_eqp_mapping_info 파일 적재 서비스입니다."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
from api.data_movement.mes_eqp_mapping_info.models import MesEqpMappingInfoLoadJob
from api.data_movement.mes_eqp_mapping_info.services import spec


@dataclass(frozen=True)
class LoadFileOutcome:
    """단일 파일 처리 결과입니다."""

    file_name: str
    status: str
    row_count: int
    replace_scope: str = spec.REPLACE_SCOPE
    error_message: str | None = None


@dataclass(frozen=True)
class LoadRunSummary:
    """mes_eqp_mapping_info 적재 실행 요약입니다."""

    outcomes: list[LoadFileOutcome]

    @property
    def processed_count(self) -> int:
        """처리한 파일 수를 반환합니다."""

        return len(self.outcomes)

    @property
    def success_count(self) -> int:
        """성공한 파일 수를 반환합니다."""

        return sum(1 for outcome in self.outcomes if outcome.status == MesEqpMappingInfoLoadJob.Status.SUCCESS)

    @property
    def failure_count(self) -> int:
        """실패한 파일 수를 반환합니다."""

        return sum(1 for outcome in self.outcomes if outcome.status == MesEqpMappingInfoLoadJob.Status.FAILED)


def _finish_job(
    *,
    job: MesEqpMappingInfoLoadJob,
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


def _create_job(*, claimed_file: ClaimedDataFile) -> MesEqpMappingInfoLoadJob:
    """선점한 파일 기준으로 적재 이력 row를 생성합니다."""

    return MesEqpMappingInfoLoadJob.objects.create(
        file_name=claimed_file.original_name,
        file_path=str(claimed_file.original_path),
        status=MesEqpMappingInfoLoadJob.Status.RUNNING,
        started_at=timezone.now(),
    )


def _read_mapping_frame(*, file_path: Path):
    """MES 매핑 deflate CSV를 spec 기준 DataFrame으로 읽습니다."""

    return read_deflate_csv_file(
        file_path=file_path,
        columns=spec.COLUMNS,
        datetime_columns=spec.DATETIME_COLUMNS,
        float_columns=spec.FLOAT_COLUMNS,
        separator=spec.FILE_SEPARATOR,
    )


def _load_claimed_file(*, claimed_file: ClaimedDataFile) -> LoadFileOutcome:
    """processing으로 선점한 매핑 파일을 대상 테이블에 전체 반영합니다."""

    job = _create_job(claimed_file=claimed_file)

    try:
        frame = _read_mapping_frame(file_path=claimed_file.working_path)
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
            status=MesEqpMappingInfoLoadJob.Status.SUCCESS,
            row_count=result.row_count,
        )
        return LoadFileOutcome(
            file_name=claimed_file.original_name,
            status=MesEqpMappingInfoLoadJob.Status.SUCCESS,
            row_count=result.row_count,
        )
    except Exception as exc:
        error_message = str(exc)
        delete_claimed_file(claimed_file=claimed_file)
        _finish_job(
            job=job,
            status=MesEqpMappingInfoLoadJob.Status.FAILED,
            row_count=0,
            error_message=error_message,
        )
        return LoadFileOutcome(
            file_name=claimed_file.original_name,
            status=MesEqpMappingInfoLoadJob.Status.FAILED,
            row_count=0,
            error_message=error_message,
        )


def _dry_run_one_file(*, file_path: Path) -> LoadFileOutcome:
    """파일 이동 없이 단일 매핑 파일을 파싱 검증합니다."""

    job = MesEqpMappingInfoLoadJob.objects.create(
        file_name=file_path.name,
        file_path=str(file_path),
        status=MesEqpMappingInfoLoadJob.Status.RUNNING,
        started_at=timezone.now(),
    )

    try:
        frame = _read_mapping_frame(file_path=file_path)
        row_count = frame.shape[0]
        if row_count == 0:
            raise ValueError(f"empty dataframe: {file_path}")

        _finish_job(
            job=job,
            status=MesEqpMappingInfoLoadJob.Status.DRY_RUN,
            row_count=row_count,
        )
        return LoadFileOutcome(
            file_name=file_path.name,
            status=MesEqpMappingInfoLoadJob.Status.DRY_RUN,
            row_count=row_count,
        )
    except Exception as exc:
        error_message = str(exc)
        _finish_job(
            job=job,
            status=MesEqpMappingInfoLoadJob.Status.FAILED,
            row_count=0,
            error_message=error_message,
        )
        return LoadFileOutcome(
            file_name=file_path.name,
            status=MesEqpMappingInfoLoadJob.Status.FAILED,
            row_count=0,
            error_message=error_message,
        )


def _load_one_file(*, file_path: Path, table_dir: Path, dry_run: bool) -> LoadFileOutcome:
    """단일 매핑 파일을 읽고 대상 테이블에 전체 반영합니다."""

    if dry_run:
        return _dry_run_one_file(file_path=file_path)

    claimed_file = claim_incoming_file(file_path=file_path, table_dir=table_dir)
    return _load_claimed_file(claimed_file=claimed_file)


def load_mes_eqp_mapping_info_files(
    *,
    data_dir: Path | str | None = None,
    dry_run: bool = False,
    limit: int | None = None,
) -> LoadRunSummary:
    """mes_eqp_mapping_info deflate CSV 파일들을 순차 적재합니다."""

    resolved_table_dir = Path(data_dir) if data_dir is not None else spec.DEFAULT_TABLE_DIR
    files = list_incoming_files(table_dir=resolved_table_dir, pattern=spec.FILE_PATTERN, limit=limit)

    outcomes = [
        _load_one_file(file_path=file_path, table_dir=resolved_table_dir, dry_run=dry_run)
        for file_path in files
    ]
    return LoadRunSummary(outcomes=outcomes)
