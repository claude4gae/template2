"""대용량 deflate CSV에서 필요한 컬럼만 추출하는 스트리밍 헬퍼입니다."""

from __future__ import annotations

import codecs
import csv
import zlib
from datetime import datetime
from pathlib import Path
from typing import Iterator, Mapping, Sequence


def iter_deflate_text_lines(
    *,
    file_path: Path,
    encoding: str = "utf-8",
    chunk_size: int = 1024 * 1024,
) -> Iterator[str]:
    """deflate 압축 파일을 줄 단위 텍스트 iterator로 변환합니다."""

    decompressor = zlib.decompressobj()
    decoder = codecs.getincrementaldecoder(encoding)(errors="replace")
    pending = ""

    with file_path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break

            text = decoder.decode(decompressor.decompress(chunk))
            pending += text
            lines = pending.splitlines(keepends=True)
            if lines and not lines[-1].endswith(("\n", "\r")):
                pending = lines.pop()
            else:
                pending = ""
            yield from lines

    pending += decoder.decode(decompressor.flush(), final=True)
    if pending:
        yield pending


def _build_selected_indexes(
    *,
    file_columns: Sequence[str],
    db_columns: Sequence[str],
    column_sources: Mapping[str, str],
) -> list[int]:
    """DB 컬럼 순서에 맞는 원본 파일 컬럼 index 목록을 생성합니다."""

    file_index = {column: index for index, column in enumerate(file_columns)}
    selected_indexes: list[int] = []
    for db_column in db_columns:
        file_column = column_sources.get(db_column, db_column)
        if file_column not in file_index:
            raise ValueError(f"파일 컬럼을 찾을 수 없습니다: {file_column}")
        selected_indexes.append(file_index[file_column])
    return selected_indexes


def _build_filter_indexes(
    *,
    file_columns: Sequence[str],
    row_filters: Mapping[str, str],
) -> dict[int, str]:
    """원본 파일 컬럼명 기반 row filter를 index 기반 dict로 변환합니다."""

    file_index = {column: index for index, column in enumerate(file_columns)}
    filter_indexes: dict[int, str] = {}
    for file_column, expected_value in row_filters.items():
        if file_column not in file_index:
            raise ValueError(f"필터 파일 컬럼을 찾을 수 없습니다: {file_column}")
        filter_indexes[file_index[file_column]] = expected_value
    return filter_indexes


def _build_excluded_filter_indexes(
    *,
    file_columns: Sequence[str],
    excluded_row_filters: Mapping[str, set[str]],
) -> dict[int, set[str]]:
    """원본 파일 컬럼명 기반 제외 filter를 index 기반 dict로 변환합니다."""

    file_index = {column: index for index, column in enumerate(file_columns)}
    filter_indexes: dict[int, set[str]] = {}
    for file_column, excluded_values in excluded_row_filters.items():
        if file_column not in file_index:
            raise ValueError(f"제외 필터 파일 컬럼을 찾을 수 없습니다: {file_column}")
        filter_indexes[file_index[file_column]] = excluded_values
    return filter_indexes


def _matches_filters(*, row: Sequence[str], filter_indexes: Mapping[int, str]) -> bool:
    """row가 모든 filter 조건을 만족하는지 확인합니다."""

    for index, expected_value in filter_indexes.items():
        if index >= len(row):
            return False
        if row[index].strip() != expected_value:
            return False
    return True


def _matches_excluded_filters(*, row: Sequence[str], filter_indexes: Mapping[int, set[str]]) -> bool:
    """row가 제외 filter 중 하나라도 만족하는지 확인합니다."""

    for index, excluded_values in filter_indexes.items():
        if index < len(row) and row[index].strip() in excluded_values:
            return True
    return False


def _build_min_datetime_filter_indexes(
    *,
    file_columns: Sequence[str],
    min_datetime_filters: Mapping[str, datetime],
) -> dict[int, datetime]:
    """원본 파일 컬럼명 기반 최소 datetime filter를 index 기반 dict로 변환합니다."""

    file_index = {column: index for index, column in enumerate(file_columns)}
    filter_indexes: dict[int, datetime] = {}
    for file_column, min_value in min_datetime_filters.items():
        if file_column not in file_index:
            raise ValueError(f"datetime 필터 파일 컬럼을 찾을 수 없습니다: {file_column}")
        filter_indexes[file_index[file_column]] = min_value
    return filter_indexes


def _parse_datetime(value: str) -> datetime | None:
    """원천 CSV datetime 문자열을 비교 가능한 datetime으로 변환합니다."""

    normalized = value.strip()
    if not normalized:
        return None

    for date_format in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d",
        "%Y%m%d%H%M%S",
        "%Y%m%d",
    ):
        try:
            return datetime.strptime(normalized, date_format)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _matches_min_datetime_filters(
    *,
    row: Sequence[str],
    filter_indexes: Mapping[int, datetime],
) -> bool:
    """row가 모든 최소 datetime filter 조건을 만족하는지 확인합니다."""

    for index, min_value in filter_indexes.items():
        if index >= len(row):
            return False
        parsed_value = _parse_datetime(row[index])
        if parsed_value is None or parsed_value < min_value:
            return False
    return True


def write_selected_deflate_csv(
    *,
    source_path: Path,
    output_path: Path,
    file_columns: Sequence[str],
    db_columns: Sequence[str],
    column_sources: Mapping[str, str] | None = None,
    row_filters: Mapping[str, str] | None = None,
    excluded_row_filters: Mapping[str, set[str]] | None = None,
    min_datetime_filters: Mapping[str, datetime] | None = None,
    separator: str = ",",
    has_header: bool = False,
) -> int:
    """deflate CSV에서 DB 적재 대상 컬럼만 추출해 새 CSV 파일로 씁니다."""

    resolved_sources = column_sources or {}
    selected_indexes = _build_selected_indexes(
        file_columns=file_columns,
        db_columns=db_columns,
        column_sources=resolved_sources,
    )
    filter_indexes = _build_filter_indexes(
        file_columns=file_columns,
        row_filters=row_filters or {},
    )
    excluded_filter_indexes = _build_excluded_filter_indexes(
        file_columns=file_columns,
        excluded_row_filters=excluded_row_filters or {},
    )
    min_datetime_filter_indexes = _build_min_datetime_filter_indexes(
        file_columns=file_columns,
        min_datetime_filters=min_datetime_filters or {},
    )
    required_width = max(selected_indexes) + 1 if selected_indexes else 0

    row_count = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output)
        reader = csv.reader(
            iter_deflate_text_lines(file_path=source_path),
            delimiter=separator,
        )
        if has_header:
            next(reader, None)

        for row_index, row in enumerate(reader, start=1):
            if not row or all(not value.strip() for value in row):
                continue
            if filter_indexes and not _matches_filters(row=row, filter_indexes=filter_indexes):
                continue
            if excluded_filter_indexes and _matches_excluded_filters(row=row, filter_indexes=excluded_filter_indexes):
                continue
            if min_datetime_filter_indexes and not _matches_min_datetime_filters(
                row=row,
                filter_indexes=min_datetime_filter_indexes,
            ):
                continue
            if len(row) < required_width:
                raise ValueError(f"CSV row {row_index} 컬럼 수가 부족합니다: {len(row)}")
            writer.writerow([row[index].strip() for index in selected_indexes])
            row_count += 1

    return row_count
