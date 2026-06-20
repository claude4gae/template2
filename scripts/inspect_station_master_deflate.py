#!/usr/bin/env python3
"""station_master deflate CSV 파일의 실제 구분자와 row 형태를 확인합니다."""

from __future__ import annotations

import argparse
import csv
import sys
import zlib
from pathlib import Path


DEFAULT_EXPECTED_COLUMNS = 52
DEFAULT_SEPARATORS = {
    "comma": ",",
    "backtick": "`",
    "ctrl_c": "\x03",
    "ctrl_a": "\x01",
    "ctrl_b": "\x02",
    "unit_sep": "\x1f",
    "tab": "\t",
    "pipe": "|",
    "semicolon": ";",
}


def _decode_deflate(file_path: Path, *, encoding: str) -> str:
    """deflate 파일을 압축 해제하고 텍스트로 변환합니다."""

    raw = file_path.read_bytes()
    try:
        payload = zlib.decompress(raw)
    except zlib.error as exc:
        raise SystemExit(f"deflate 압축 해제 실패: {exc}") from exc
    return payload.decode(encoding, errors="replace")


def _preview(value: str, *, limit: int = 220) -> str:
    """제어문자와 긴 문자열을 터미널에서 읽기 쉽게 줄입니다."""

    normalized = value.replace("\x03", "\\x03").replace("\x01", "\\x01").replace("\x02", "\\x02")
    normalized = normalized.replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n")
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit]}..."


def _split_row(line: str, *, separator: str) -> list[str]:
    """csv 모듈로 한 row를 지정 구분자 기준 분리합니다."""

    return next(csv.reader([line], delimiter=separator))


def _print_separator_report(
    *,
    lines: list[str],
    expected_columns: int,
    separators: dict[str, str],
) -> str | None:
    """후보 구분자별 컬럼 수를 출력하고 기대 컬럼 수와 맞는 후보를 반환합니다."""

    matched_separator: str | None = None
    print("\n== delimiter candidates ==")
    for name, separator in separators.items():
        widths = [len(_split_row(line, separator=separator)) for line in lines]
        unique_widths = sorted(set(widths))
        marker = "MATCH" if unique_widths == [expected_columns] else ""
        if marker and matched_separator is None:
            matched_separator = separator
        print(f"{name:10s} {repr(separator):8s} widths={widths} unique={unique_widths} {marker}")
    return matched_separator


def _print_row_sample(*, line: str, separator: str, expected_columns: int) -> None:
    """선택 구분자로 나눈 첫 row의 컬럼별 샘플을 출력합니다."""

    fields = _split_row(line, separator=separator)
    print("\n== first row fields ==")
    print(f"field_count={len(fields)} expected={expected_columns} separator={repr(separator)}")
    for index, value in enumerate(fields[: min(len(fields), expected_columns, 80)], start=1):
        print(f"{index:02d}: {_preview(value, limit=120)}")
    if len(fields) > 80:
        print(f"... {len(fields) - 80} more fields")


def main() -> int:
    """CLI entrypoint입니다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="확인할 *_STATION_MASTER_*.csv.deflate 파일 경로")
    parser.add_argument("--expected-columns", type=int, default=DEFAULT_EXPECTED_COLUMNS)
    parser.add_argument("--encoding", default="utf-8")
    parser.add_argument("--rows", type=int, default=5, help="구분자 후보를 검사할 non-empty row 수")
    args = parser.parse_args()

    text = _decode_deflate(args.file, encoding=args.encoding)
    lines = [line for line in text.splitlines() if line.strip()]
    sample_lines = lines[: args.rows]

    print("== file ==")
    print(f"path={args.file}")
    print(f"decompressed_chars={len(text)}")
    print(f"non_empty_lines={len(lines)}")
    if not sample_lines:
        print("non-empty row가 없습니다.")
        return 1

    print("\n== first non-empty row preview ==")
    print(_preview(sample_lines[0]))

    matched_separator = _print_separator_report(
        lines=sample_lines,
        expected_columns=args.expected_columns,
        separators=DEFAULT_SEPARATORS,
    )
    if matched_separator is None:
        print("\n기대 컬럼 수와 정확히 맞는 구분자를 찾지 못했습니다.")
        print("파일 원본의 실제 컬럼 수, header 포함 여부, quote escape 상태를 확인하세요.")
        return 2

    _print_row_sample(
        line=sample_lines[0],
        separator=matched_separator,
        expected_columns=args.expected_columns,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
