"""ctttm_workorder_list 전용 고속 deflate CSV 추출기입니다."""

from __future__ import annotations

import csv
import zlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator, Mapping, Sequence

from api.data_movement.common.services.streaming_csv import parse_csv_datetime


@dataclass(frozen=True)
class FastCsvPlan:
    """원천 row에서 필요한 컬럼 index만 담은 추출 계획입니다."""

    selected_indexes: list[int]
    row_filter_indexes: dict[int, bytes]
    min_datetime_indexes: dict[int, datetime]

    @property
    def max_required_index(self) -> int:
        """필터와 적재에 필요한 가장 큰 원천 컬럼 index를 반환합니다."""

        indexes = [
            *self.selected_indexes,
            *self.row_filter_indexes.keys(),
            *self.min_datetime_indexes.keys(),
        ]
        return max(indexes) if indexes else 0


def iter_deflate_byte_lines(
    *,
    file_path: Path,
    chunk_size: int = 1024 * 1024,
) -> Iterator[bytes]:
    """deflate 압축 파일을 decode 없이 bytes line iterator로 변환합니다."""

    decompressor = zlib.decompressobj()
    pending = b""

    with file_path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break

            pending += decompressor.decompress(chunk)
            lines = pending.splitlines(keepends=True)
            if lines and not lines[-1].endswith((b"\n", b"\r")):
                pending = lines.pop()
            else:
                pending = b""
            yield from lines

    pending += decompressor.flush()
    if pending:
        yield pending


def build_fast_csv_plan(
    *,
    file_columns: Sequence[str],
    db_columns: Sequence[str],
    column_sources: Mapping[str, str],
    row_filters: Mapping[str, str],
    min_datetime_filters: Mapping[str, datetime],
) -> FastCsvPlan:
    """컬럼명 기반 설정을 bytes 추출에 사용할 index 계획으로 변환합니다."""

    file_index = {column: index for index, column in enumerate(file_columns)}
    selected_indexes = [
        file_index[column_sources.get(db_column, db_column)]
        for db_column in db_columns
    ]
    row_filter_indexes = {
        file_index[file_column]: expected_value.encode("utf-8")
        for file_column, expected_value in row_filters.items()
    }
    min_datetime_indexes = {
        file_index[file_column]: min_value
        for file_column, min_value in min_datetime_filters.items()
    }
    return FastCsvPlan(
        selected_indexes=selected_indexes,
        row_filter_indexes=row_filter_indexes,
        min_datetime_indexes=min_datetime_indexes,
    )


def _matches_row_filters(*, fields: Sequence[bytes], plan: FastCsvPlan) -> bool:
    """bytes row가 단순 문자열 필터를 통과하는지 확인합니다."""

    for index, expected_value in plan.row_filter_indexes.items():
        if index >= len(fields) or fields[index].strip() != expected_value:
            return False
    return True


def _matches_datetime_filters(*, fields: Sequence[bytes], plan: FastCsvPlan) -> bool:
    """bytes row가 datetime 최소값 필터를 통과하는지 확인합니다."""

    for index, min_value in plan.min_datetime_indexes.items():
        if index >= len(fields):
            return False
        raw_value = fields[index].strip().decode("utf-8", errors="replace")
        parsed_value = parse_csv_datetime(raw_value)
        if parsed_value is None or parsed_value < min_value:
            return False
    return True


def write_fast_selected_deflate_csv(
    *,
    source_path: Path,
    output_path: Path,
    plan: FastCsvPlan,
    separator: str,
) -> int:
    """deflate CSV에서 필요한 index까지만 분리해 선택 컬럼 CSV를 생성합니다."""

    separator_bytes = separator.encode("utf-8")
    max_required_index = plan.max_required_index
    row_count = 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output)
        for row_index, raw_line in enumerate(iter_deflate_byte_lines(file_path=source_path), start=1):
            line = raw_line.rstrip(b"\r\n")
            if not line.strip():
                continue

            fields = line.split(separator_bytes, maxsplit=max_required_index + 1)
            if not _matches_row_filters(fields=fields, plan=plan):
                continue
            if not _matches_datetime_filters(fields=fields, plan=plan):
                continue
            if any(index >= len(fields) for index in plan.selected_indexes):
                raise ValueError(f"CSV row {row_index} 컬럼 수가 부족합니다: {len(fields)}")

            writer.writerow(
                [
                    fields[index].strip().decode("utf-8", errors="replace")
                    for index in plan.selected_indexes
                ]
            )
            row_count += 1

    return row_count
