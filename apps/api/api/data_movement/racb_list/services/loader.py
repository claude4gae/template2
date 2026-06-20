"""racb_list 파일 적재 서비스입니다."""

from __future__ import annotations

import csv
import tempfile
from dataclasses import dataclass
from pathlib import Path

from django.db import connection, transaction
from django.utils import timezone

from api.data_movement.common.services.file_loader import (
    ClaimedDataFile,
    claim_incoming_file,
    delete_claimed_file,
    list_incoming_files,
)
from api.data_movement.common.services.streaming_csv import iter_deflate_text_lines, parse_csv_datetime
from api.data_movement.racb_list.models import RacbListLoadJob
from api.data_movement.racb_list.services import spec


@dataclass(frozen=True)
class LoadFileOutcome:
    """단일 파일 처리 결과입니다."""

    file_name: str
    status: str
    row_count: int
    error_message: str | None = None


@dataclass(frozen=True)
class LoadRunSummary:
    """racb_list 적재 실행 요약입니다."""

    outcomes: list[LoadFileOutcome]

    @property
    def processed_count(self) -> int:
        """처리한 파일 수를 반환합니다."""

        return len(self.outcomes)

    @property
    def success_count(self) -> int:
        """성공한 파일 수를 반환합니다."""

        return sum(1 for outcome in self.outcomes if outcome.status == RacbListLoadJob.Status.SUCCESS)

    @property
    def failure_count(self) -> int:
        """실패한 파일 수를 반환합니다."""

        return sum(1 for outcome in self.outcomes if outcome.status == RacbListLoadJob.Status.FAILED)


def _finish_job(
    *,
    job: RacbListLoadJob,
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


def _create_job(*, file_name: str, file_path: Path) -> RacbListLoadJob:
    """파일 기준으로 적재 이력 row를 생성합니다."""

    return RacbListLoadJob.objects.create(
        file_name=file_name,
        file_path=str(file_path),
        status=RacbListLoadJob.Status.RUNNING,
        started_at=timezone.now(),
    )


def _quote_identifier(identifier: str) -> str:
    """SQL identifier를 quote 처리합니다."""

    return connection.ops.quote_name(identifier)


def _parse_required_datetime(*, value: str, column: str, row_index: int):
    """필수 datetime 문자열을 파싱하고 실패 시 파일 오류로 처리합니다."""

    parsed = parse_csv_datetime(value)
    if parsed is None:
        raise ValueError(f"CSV row {row_index} {column} 값을 datetime으로 변환할 수 없습니다: {value}")
    return parsed


def _copy_selected_file_to_temp(*, cursor, selected_csv_path: Path) -> None:
    """선별 CSV 파일을 temp table로 COPY 합니다."""

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


def _select_latest_rows(*, source_path: Path) -> dict[str, list[str]]:
    """원본 deflate CSV에서 중복 제거 후 c_racb_id별 최신 row를 선택합니다."""

    source_indexes = {column: index for index, column in enumerate(spec.FILE_COLUMNS)}
    required_width = len(spec.FILE_COLUMNS)
    seen_rows: set[tuple[str, ...]] = set()
    latest_rows: dict[str, tuple[object, list[str]]] = {}

    reader = csv.reader(iter_deflate_text_lines(file_path=source_path), delimiter=spec.FILE_SEPARATOR)
    for row_index, row in enumerate(reader, start=1):
        if not row or all(not value.strip() for value in row):
            continue
        if len(row) < required_width:
            raise ValueError(f"CSV row {row_index} 컬럼 수가 부족합니다: {len(row)}")

        normalized_row = [value.strip() for value in row[:required_width]]
        if row_index == 1 and [value.lower() for value in normalized_row] == spec.FILE_COLUMNS:
            continue
        row_key = tuple(normalized_row)
        if row_key in seen_rows:
            continue
        seen_rows.add(row_key)

        c_racb_id = normalized_row[source_indexes["c_racb_id"]]
        if not c_racb_id:
            continue

        update_date = _parse_required_datetime(
            value=normalized_row[source_indexes["update_date"]],
            column="update_date",
            row_index=row_index,
        )
        current = latest_rows.get(c_racb_id)
        if current is None or update_date > current[0]:
            latest_rows[c_racb_id] = (update_date, normalized_row)

    return {c_racb_id: row for c_racb_id, (_, row) in latest_rows.items()}


def _build_selected_values(*, row: list[str], eqp_cb: str, source_indexes: dict[str, int]) -> list[str]:
    """전처리된 row를 DB column 순서 값으로 변환합니다."""

    values = []
    for column in spec.DB_COLUMNS:
        if column == "eqp_cb":
            values.append(eqp_cb)
        else:
            values.append(row[source_indexes[column]])
    return values


def _write_selected_csv(*, source_path: Path, output_dir: Path) -> tuple[Path, int]:
    """원본 deflate CSV에서 최신 RACB row를 설비별로 펼친 임시 CSV를 생성합니다."""

    source_indexes = {column: index for index, column in enumerate(spec.FILE_COLUMNS)}
    latest_rows = _select_latest_rows(source_path=source_path)

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".selected.csv",
        dir=output_dir,
        delete=False,
        newline="",
    ) as handle:
        selected_path = Path(handle.name)
        writer = csv.writer(handle)
        row_count = 0

        for row in latest_rows.values():
            create_date = row[source_indexes["create_date"]]
            if not create_date:
                continue
            eqp_values = [
                eqp_id.strip()
                for eqp_id in row[source_indexes["eqp_ids"]].split(",")
                if eqp_id.strip()
            ]
            for eqp_cb in eqp_values:
                writer.writerow(_build_selected_values(row=row, eqp_cb=eqp_cb, source_indexes=source_indexes))
                row_count += 1

    return selected_path, row_count


def _replace_rows(*, selected_csv_path: Path) -> None:
    """파일에 포함된 c_racb_id 범위를 삭제한 뒤 전처리 결과를 다시 저장합니다."""

    quoted_table = _quote_identifier(spec.TABLE_NAME)
    quoted_temp = _quote_identifier(spec.TEMP_TABLE_NAME)
    temp_columns_sql = ", ".join(f"{_quote_identifier(column)} text" for column in spec.DB_COLUMNS)
    quoted_columns = ", ".join(_quote_identifier(column) for column in spec.DB_COLUMNS)

    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {quoted_temp}")
            cursor.execute(
                f"""
                CREATE TEMP TABLE {quoted_temp}
                ({temp_columns_sql})
                ON COMMIT DROP
                """
            )
            _copy_selected_file_to_temp(cursor=cursor, selected_csv_path=selected_csv_path)
            cursor.execute(
                f"""
                DELETE FROM {quoted_table}
                WHERE c_racb_id IN (
                    SELECT DISTINCT NULLIF(c_racb_id, '')
                    FROM {quoted_temp}
                    WHERE NULLIF(c_racb_id, '') IS NOT NULL
                )
                """
            )
            cursor.execute(
                f"""
                INSERT INTO {quoted_table} ({quoted_columns})
                SELECT DISTINCT ON (NULLIF(src.c_racb_id, ''), NULLIF(src.eqp_cb, ''))
                    NULLIF(src.c_racb_id, ''),
                    NULLIF(src.o_racb_id, ''),
                    NULLIF(src.gbm, ''),
                    NULLIF(src.line, ''),
                    NULLIF(src.line_id, ''),
                    NULLIF(src.area, ''),
                    NULLIF(src.sdwt_name, ''),
                    NULLIF(src.title, ''),
                    NULLIF(src.sub_title, ''),
                    NULLIF(src.fiveone, ''),
                    NULLIF(src.racb_type_cd, ''),
                    NULLIF(src.major_category, ''),
                    NULLIF(src.minor_category, ''),
                    NULLIF(src.eqp_cb, ''),
                    NULLIF(src.prc_groups, ''),
                    NULLIF(src.level_data, ''),
                    NULLIF(src.status_code, ''),
                    NULLIF(src.status, ''),
                    NULLIF(src.detail_type_cd, ''),
                    NULLIF(src.change_cd, ''),
                    NULLIF(src.fdc, ''),
                    NULLIF(src.npw, ''),
                    NULLIF(src.metro, ''),
                    NULLIF(src.defect, ''),
                    NULLIF(src.create_date, '')::timestamp,
                    NULLIF(src.due_date, '')::timestamp,
                    NULLIF(src.user_name, ''),
                    NULLIF(src.create_user, ''),
                    NULLIF(src.update_date, '')::timestamp,
                    NULLIF(src.update_user, ''),
                    NULLIF(src.sub_area, '')
                FROM {quoted_temp} src
                WHERE NULLIF(src.c_racb_id, '') IS NOT NULL
                  AND NULLIF(src.eqp_cb, '') IS NOT NULL
                  AND NULLIF(src.create_date, '') IS NOT NULL
                  AND NULLIF(src.update_date, '') IS NOT NULL
                ORDER BY
                    NULLIF(src.c_racb_id, ''),
                    NULLIF(src.eqp_cb, ''),
                    NULLIF(src.update_date, '')::timestamp DESC
                """
            )


def _load_claimed_file(*, claimed_file: ClaimedDataFile) -> LoadFileOutcome:
    """processing으로 선점한 racb_list 파일을 범위 교체 방식으로 반영합니다."""

    selected_path: Path | None = None
    job = _create_job(file_name=claimed_file.original_name, file_path=claimed_file.original_path)

    try:
        selected_path, row_count = _write_selected_csv(
            source_path=claimed_file.working_path,
            output_dir=claimed_file.working_path.parent,
        )
        if row_count == 0:
            raise ValueError(f"empty dataframe: {claimed_file.original_path}")

        _replace_rows(selected_csv_path=selected_path)
        _finish_job(job=job, status=RacbListLoadJob.Status.SUCCESS, row_count=row_count)
        return LoadFileOutcome(
            file_name=claimed_file.original_name,
            status=RacbListLoadJob.Status.SUCCESS,
            row_count=row_count,
        )
    except Exception as exc:
        error_message = str(exc)
        _finish_job(
            job=job,
            status=RacbListLoadJob.Status.FAILED,
            row_count=0,
            error_message=error_message,
        )
        return LoadFileOutcome(
            file_name=claimed_file.original_name,
            status=RacbListLoadJob.Status.FAILED,
            row_count=0,
            error_message=error_message,
        )
    finally:
        if selected_path is not None:
            selected_path.unlink(missing_ok=True)
        delete_claimed_file(claimed_file=claimed_file)


def _dry_run_one_file(*, file_path: Path) -> LoadFileOutcome:
    """파일 이동 없이 단일 racb_list 파일을 파싱 검증합니다."""

    selected_path: Path | None = None
    job = _create_job(file_name=file_path.name, file_path=file_path)

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            selected_path, row_count = _write_selected_csv(
                source_path=file_path,
                output_dir=Path(temp_dir),
            )
            if row_count == 0:
                raise ValueError(f"empty dataframe: {file_path}")
        _finish_job(job=job, status=RacbListLoadJob.Status.DRY_RUN, row_count=row_count)
        return LoadFileOutcome(
            file_name=file_path.name,
            status=RacbListLoadJob.Status.DRY_RUN,
            row_count=row_count,
        )
    except Exception as exc:
        error_message = str(exc)
        _finish_job(
            job=job,
            status=RacbListLoadJob.Status.FAILED,
            row_count=0,
            error_message=error_message,
        )
        return LoadFileOutcome(
            file_name=file_path.name,
            status=RacbListLoadJob.Status.FAILED,
            row_count=0,
            error_message=error_message,
        )
    finally:
        if selected_path is not None:
            selected_path.unlink(missing_ok=True)


def load_racb_list_files(
    *,
    data_dir: Path | str | None = None,
    dry_run: bool = False,
    limit: int | None = None,
) -> LoadRunSummary:
    """racb_list deflate CSV 파일들을 순차 적재합니다."""

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
