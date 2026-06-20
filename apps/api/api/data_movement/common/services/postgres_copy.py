"""PostgreSQL COPY 기반 교체 적재 공통 헬퍼입니다."""

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import Any, Sequence

from django.db import connection

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class CopyReplaceResult:
    """COPY 교체 적재 결과입니다."""

    row_count: int
    column_count: int
    replace_values: list[Any]


@dataclass(frozen=True)
class CopyFullReplaceResult:
    """COPY 전체 교체 적재 결과입니다."""

    row_count: int
    column_count: int


def _quote_identifier(identifier: str) -> str:
    """단일 SQL identifier를 안전하게 quote 처리합니다."""

    if not _IDENTIFIER_RE.fullmatch(identifier):
        raise ValueError(f"허용되지 않는 SQL identifier입니다: {identifier}")
    return connection.ops.quote_name(identifier)


def _quote_columns(columns: Sequence[str]) -> str:
    """컬럼 목록을 SQL column list 문자열로 변환합니다."""

    return ", ".join(_quote_identifier(column) for column in columns)


def extract_replace_values(*, frame: Any, replace_column: str) -> list[Any]:
    """DataFrame에서 교체 기준 컬럼의 고유 값을 추출합니다."""

    values = (
        frame.select(replace_column)
        .drop_nulls()
        .unique()
        .to_series()
        .to_list()
    )
    return [value for value in values if value not in ("", None)]


def _write_frame_csv(*, frame: Any) -> io.StringIO:
    """COPY 입력용 CSV 버퍼를 생성합니다."""

    buffer = io.StringIO()
    frame.write_csv(buffer, include_header=False, separator=",", null_value="")
    buffer.seek(0)
    return buffer


def copy_replace_rows(
    *,
    frame: Any,
    table_name: str,
    columns: Sequence[str],
    replace_column: str,
    temp_table_name: str,
) -> CopyReplaceResult:
    """temp table과 COPY를 사용해 기준 컬럼 단위로 대상 테이블을 교체 적재합니다."""

    row_count, column_count = frame.shape
    if row_count == 0:
        raise ValueError("적재할 DataFrame이 비어 있습니다.")

    replace_values = extract_replace_values(frame=frame, replace_column=replace_column)
    if not replace_values:
        raise ValueError(f"{replace_column} 값이 없습니다.")

    quoted_table = _quote_identifier(table_name)
    quoted_temp_table = _quote_identifier(temp_table_name)
    quoted_columns = _quote_columns(columns)
    quoted_replace_column = _quote_identifier(replace_column)
    buffer = _write_frame_csv(frame=frame)

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            CREATE TEMP TABLE {quoted_temp_table}
            ON COMMIT DROP
            AS
            SELECT {quoted_columns}
            FROM {quoted_table}
            WITH NO DATA
            """
        )

        copy_cursor = getattr(cursor, "cursor", cursor)
        if not hasattr(copy_cursor, "copy"):
            raise RuntimeError("psycopg3 COPY API를 사용할 수 없습니다.")

        copy_sql = f"""
            COPY {quoted_temp_table} ({quoted_columns})
            FROM STDIN
            WITH (
                FORMAT CSV,
                NULL '',
                QUOTE '"',
                ESCAPE '"'
            )
        """
        with copy_cursor.copy(copy_sql) as copy:
            copy.write(buffer.getvalue())

        cursor.execute(
            f"""
            DELETE FROM {quoted_table}
            WHERE {quoted_replace_column} = ANY(%s)
            """,
            [replace_values],
        )
        cursor.execute(
            f"""
            INSERT INTO {quoted_table} ({quoted_columns})
            SELECT {quoted_columns}
            FROM {quoted_temp_table}
            """
        )

    return CopyReplaceResult(
        row_count=row_count,
        column_count=column_count,
        replace_values=replace_values,
    )


def copy_full_replace_rows(
    *,
    frame: Any,
    table_name: str,
    columns: Sequence[str],
    temp_table_name: str,
) -> CopyFullReplaceResult:
    """temp table과 COPY를 사용해 대상 테이블을 전체 교체 적재합니다."""

    row_count, column_count = frame.shape
    if row_count == 0:
        raise ValueError("적재할 DataFrame이 비어 있습니다.")

    quoted_table = _quote_identifier(table_name)
    quoted_temp_table = _quote_identifier(temp_table_name)
    quoted_columns = _quote_columns(columns)
    buffer = _write_frame_csv(frame=frame)

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            CREATE TEMP TABLE {quoted_temp_table}
            ON COMMIT DROP
            AS
            SELECT {quoted_columns}
            FROM {quoted_table}
            WITH NO DATA
            """
        )

        copy_cursor = getattr(cursor, "cursor", cursor)
        if not hasattr(copy_cursor, "copy"):
            raise RuntimeError("psycopg3 COPY API를 사용할 수 없습니다.")

        copy_sql = f"""
            COPY {quoted_temp_table} ({quoted_columns})
            FROM STDIN
            WITH (
                FORMAT CSV,
                NULL '',
                QUOTE '"',
                ESCAPE '"'
            )
        """
        with copy_cursor.copy(copy_sql) as copy:
            copy.write(buffer.getvalue())

        cursor.execute(f"DELETE FROM {quoted_table}")
        cursor.execute(
            f"""
            INSERT INTO {quoted_table} ({quoted_columns})
            SELECT {quoted_columns}
            FROM {quoted_temp_table}
            """
        )

    return CopyFullReplaceResult(row_count=row_count, column_count=column_count)
