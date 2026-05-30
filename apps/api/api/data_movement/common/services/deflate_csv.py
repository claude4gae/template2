"""deflate CSV 파일을 Polars DataFrame으로 읽는 공통 헬퍼입니다."""

from __future__ import annotations

import io
import zlib
from pathlib import Path
from typing import Any, Sequence


def _load_polars() -> Any:
    """Polars 의존성을 지연 로드하고 누락 시 명확한 오류를 발생시킵니다."""

    try:
        import polars as pl
    except ImportError as exc:  # pragma: no cover - 배포 의존성 누락 방어
        raise RuntimeError("polars 패키지가 필요합니다. apps/api/requirements.txt를 설치하세요.") from exc
    return pl


def read_deflate_csv_file(
    *,
    file_path: Path,
    columns: Sequence[str],
    datetime_columns: Sequence[str],
    float_columns: Sequence[str],
    separator: str = "\x03",
) -> Any:
    """deflate 압축 CSV를 읽고 테이블 spec 기준으로 타입을 변환합니다."""

    pl = _load_polars()

    with file_path.open("rb") as handle:
        raw = zlib.decompress(handle.read())

    frame = pl.read_csv(
        io.BytesIO(raw),
        separator=separator,
        has_header=False,
        new_columns=list(columns),
        encoding="utf8-lossy",
        null_values=["null", "NULL", ""],
        schema_overrides={column: pl.Utf8 for column in columns},
        ignore_errors=True,
        truncate_ragged_lines=True,
    )

    datetime_exprs = [
        pl.col(column).str.strip_chars().str.strptime(pl.Datetime, strict=False)
        for column in datetime_columns
    ]
    if datetime_exprs:
        frame = frame.with_columns(datetime_exprs)

    float_exprs = [
        pl.col(column).str.strip_chars().cast(pl.Float64, strict=False)
        for column in float_columns
    ]
    if float_exprs:
        frame = frame.with_columns(float_exprs)

    return frame
