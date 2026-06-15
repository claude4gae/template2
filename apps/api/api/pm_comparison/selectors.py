# =============================================================================
# 모듈: PM SPIDER 파일 셀렉터
# 주요 함수: iter_raw_files, iter_score_files, iter_decomp_files, collect_partition_options, read_parquet
# 주요 가정: score_data/decomp_data는 PM_COMPARISON_DATA_ROOT/result 아래에 위치합니다.
# =============================================================================
from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Iterable, Sequence

from django.conf import settings

import pandas as pd

RAW_DIR_NAME   = "raw_data"
SCORE_DIR_NAME = "score_data"
DECOMP_DIR_NAME = "decomp_data"

RAW_PARTITION_KEYS = [
    "line_id",
    "eqp_id",
    "fdc_bin",
    "type",
    "dt",
    "ppid",
    "recipe_id",
    "data_source",
    "trace_param_name",
]

SCORE_PARTITION_KEYS = [
    "line_id",
    "eqp_id",
    "chamber_id",
    "type",
    "data_type",
]

# decomp_data: shape.parquet / jitter.parquet (DASHBOARD_SPEC §2)
DECOMP_PARTITION_KEYS = [
    "line_id",
    "eqp_id",
    "chamber_id",
    "type",
    "comp_dt",
    "param",
    "ch_step",
]

PARTITION_KEYS = sorted(set([*RAW_PARTITION_KEYS, *SCORE_PARTITION_KEYS, *DECOMP_PARTITION_KEYS]))

REQUEST_TO_RAW_PARTITION = {
    "lineId": "line_id",
    "eqpId": "eqp_id",
    "fdcBin": "fdc_bin",
    "type": "type",
    "ppid": "ppid",
    "recipeId": "recipe_id",
}

REQUEST_TO_SCORE_PARTITION = {
    "lineId": "line_id",
    "eqpId": "eqp_id",
    "chamberId": "chamber_id",
    "type": "type",
}

REQUEST_TO_DECOMP_PARTITION = {
    "lineId": "line_id",
    "eqpId": "eqp_id",
    "chamberId": "chamber_id",
    "type": "type",
}


def get_data_root() -> Path:
    """PM SPIDER 데이터 루트 경로를 반환합니다."""

    return Path(settings.PM_COMPARISON_DATA_ROOT).expanduser().resolve()


def ensure_data_root() -> Path:
    """데이터 루트가 조회 가능한 디렉터리인지 확인합니다."""

    root = get_data_root()
    if not root.exists():
        raise FileNotFoundError(f"PM SPIDER 데이터 경로를 찾을 수 없습니다: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"PM SPIDER 데이터 경로가 폴더가 아닙니다: {root}")
    return root


def ensure_dataset_root(dataset_name: str) -> Path:
    """raw_data 또는 score_data 데이터셋 루트를 반환합니다."""

    root = ensure_data_root() / dataset_name
    if not root.exists():
        raise FileNotFoundError(f"PM SPIDER {dataset_name} 경로를 찾을 수 없습니다: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"PM SPIDER {dataset_name} 경로가 폴더가 아닙니다: {root}")
    return root


def parse_partition_values(path: Path) -> dict[str, str]:
    """경로에서 key=value partition 값을 추출합니다."""

    values: dict[str, str] = {}
    for part in path.parts:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        if key in PARTITION_KEYS and value:
            values[key] = value
    return values


def _safe_relative_file(path: Path, root: Path) -> Path | None:
    """루트 내부 일반 파일만 반환합니다."""

    try:
        resolved = path.resolve()
        resolved.relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    if not resolved.is_file():
        return None
    return resolved


def _segment(key: str, value: str | None) -> str:
    """partition glob segment를 생성합니다."""

    if value:
        return f"{key}={value}"
    return f"{key}=*"


def _partition_filters(selection: dict[str, object], mapping: dict[str, str]) -> dict[str, str | None]:
    """요청 필드를 partition key 기준 필터로 변환합니다."""

    filters: dict[str, str | None] = {}
    for request_key, partition_key in mapping.items():
        raw_value = selection.get(request_key)
        filters[partition_key] = str(raw_value) if raw_value else None
    return filters


def _iter_partition_files(
    root: Path,
    partition_keys: Sequence[str],
    filters: dict[str, str | None],
    *,
    max_files: int,
) -> Iterable[Path]:
    """partition key 순서와 필터에 맞는 Parquet 후보 파일을 순회합니다."""

    partition_pattern = "/".join(_segment(key, filters.get(key)) for key in partition_keys)
    leaf_patterns = ["*.parquet", "*/*.parquet", "*/*/*.parquet"]
    seen: set[Path] = set()
    for leaf_pattern in leaf_patterns:
        for path in root.glob(f"{partition_pattern}/{leaf_pattern}"):
            safe_path = _safe_relative_file(path, root)
            if safe_path is None or safe_path in seen:
                continue
            seen.add(safe_path)
            yield safe_path
            if len(seen) >= max_files:
                return


def iter_raw_files(
    selection: dict[str, object],
    *,
    data_source: str,
    trace_param_names: Sequence[str] | None = None,
) -> Iterable[Path]:
    """raw_data 아래에서 요청 조건에 맞는 Parquet 후보 파일을 순회합니다. raw_data 없으면 빈 결과."""

    try:
        root = ensure_dataset_root(RAW_DIR_NAME)
    except (FileNotFoundError, NotADirectoryError):
        return
    filters = _partition_filters(selection, REQUEST_TO_RAW_PARTITION)
    filters["data_source"] = data_source

    dt_values = [str(value) for value in selection.get("dtValues", []) if value]
    trace_values = [str(value) for value in trace_param_names or [] if value]
    dt_candidates = dt_values or [None]
    trace_candidates = trace_values or [None]
    max_files = int(getattr(settings, "PM_COMPARISON_MAX_FILES", 400))
    seen: set[Path] = set()

    # Partition key variants: with and without trace_param_name (for sources that don't use it)
    _keys_with_param  = RAW_PARTITION_KEYS
    _keys_no_param    = [k for k in RAW_PARTITION_KEYS if k != "trace_param_name"]

    for dt_value in dt_candidates:
        filters["dt"] = dt_value
        for trace_value in trace_candidates:
            filters["trace_param_name"] = trace_value
            # Try full keys first, then without trace_param_name (e.g. oes_processed)
            for partition_keys in (_keys_with_param, _keys_no_param):
                if partition_keys is _keys_no_param and trace_value is not None:
                    continue  # only fall back when no specific param requested
                for path in _iter_partition_files(root, partition_keys, filters, max_files=max_files):
                    if path in seen:
                        continue
                    seen.add(path)
                    yield path
                    if len(seen) >= max_files:
                        return


def iter_score_files(selection: dict[str, object], *, data_type: str) -> Iterable[Path]:
    """score_data 아래에서 요청 조건에 맞는 Parquet 후보 파일을 순회합니다."""

    root = ensure_dataset_root(SCORE_DIR_NAME)
    filters = _partition_filters(selection, REQUEST_TO_SCORE_PARTITION)
    # fdcBin과 chamber_id는 동일 — chamberId 미지정 시 fdcBin으로 대체
    if not filters.get("chamber_id"):
        fdc_bin = selection.get("fdcBin")
        if fdc_bin:
            filters["chamber_id"] = str(fdc_bin)
    filters["data_type"] = data_type
    max_files = int(getattr(settings, "PM_COMPARISON_MAX_FILES", 400))
    seen: set[Path] = set()
    key_variants = [SCORE_PARTITION_KEYS]
    if not filters.get("chamber_id"):
        key_variants.append([key for key in SCORE_PARTITION_KEYS if key != "chamber_id"])
    for partition_keys in key_variants:
        for path in _iter_partition_files(root, partition_keys, filters, max_files=max_files):
            if path in seen:
                continue
            seen.add(path)
            yield path
            if len(seen) >= max_files:
                return


def iter_decomp_files(
    selection: dict[str, object],
    *,
    comp_dt: str | None = None,
    param_names: Sequence[str] | None = None,
    file_name: str = "shape.parquet",
) -> Iterable[Path]:
    """decomp_data 아래에서 shape.parquet / jitter.parquet 파일을 순회합니다.

    DASHBOARD_SPEC §2 경로:
      decomp_data/line_id={}/eqp_id={}/chamber_id={}/type={}/comp_dt={}/param={}/ch_step={}/{file_name}
    """

    try:
        root = ensure_dataset_root(DECOMP_DIR_NAME)
    except (FileNotFoundError, NotADirectoryError):
        return

    filters = _partition_filters(selection, REQUEST_TO_DECOMP_PARTITION)
    filters["comp_dt"] = comp_dt or None
    max_files = int(getattr(settings, "PM_COMPARISON_MAX_FILES", 400))
    seen: set[Path] = set()

    param_values = [str(p) for p in (param_names or []) if p]
    param_candidates = param_values or [None]

    for param in param_candidates:
        filters["param"] = param
        for path in _iter_partition_files(root, DECOMP_PARTITION_KEYS, filters, max_files=max_files):
            if path in seen:
                continue
            if path.name != file_name:
                continue
            seen.add(path)
            yield path
            if len(seen) >= max_files:
                return


def _scan_partition_dirs(root: Path, keys: list[str], max_dirs: int) -> dict[str, set[str]]:
    """디렉터리 트리에서 key=value partition 값을 수집합니다."""

    options: dict[str, set[str]] = {key: set() for key in keys}
    queue: deque[tuple[Path, int]] = deque([(root, 0)])
    visited = 0
    while queue and visited < max_dirs:
        current, depth = queue.popleft()
        if depth >= len(keys):
            continue
        try:
            children = sorted(path for path in current.iterdir() if path.is_dir())
        except OSError:
            continue
        visited += len(children)
        for child in children:
            partition = parse_partition_values(child)
            for key, value in partition.items():
                if key in options:
                    options[key].add(value)
            queue.append((child, depth + 1))
            if visited >= max_dirs:
                break
    return options


def collect_partition_options() -> dict[str, list[str]]:
    """raw_data 아래 partition 값을 수집합니다. raw_data 없으면 score_data에서 대체합니다."""

    max_dirs = int(getattr(settings, "PM_COMPARISON_MAX_META_DIRS", 5000))
    try:
        raw_root = ensure_dataset_root(RAW_DIR_NAME)
        options = _scan_partition_dirs(raw_root, RAW_PARTITION_KEYS, max_dirs)
    except (FileNotFoundError, NotADirectoryError):
        # raw_data 없음 — score_data partition 값으로 대체
        options = {key: set() for key in RAW_PARTITION_KEYS}
        try:
            score_root = ensure_dataset_root(SCORE_DIR_NAME)
            score_opts = _scan_partition_dirs(score_root, SCORE_PARTITION_KEYS, max_dirs)
            # score chamber_id → fdc_bin 으로 노출
            options["line_id"].update(score_opts.get("line_id", set()))
            options["eqp_id"].update(score_opts.get("eqp_id", set()))
            options["fdc_bin"].update(score_opts.get("chamber_id", set()))
        except (FileNotFoundError, NotADirectoryError):
            pass

    return {key: sorted(values) for key, values in options.items()}


def read_parquet(path: Path, columns: Sequence[str] | None = None) -> pd.DataFrame:
    """Parquet 파일을 읽고 요청 컬럼이 없으면 전체 컬럼으로 fallback합니다."""

    if columns:
        try:
            return pd.read_parquet(path, engine="pyarrow", columns=list(columns))
        except Exception:
            frame = pd.read_parquet(path, engine="pyarrow")
            available = [column for column in columns if column in frame.columns]
            if available:
                return frame[available]
            return frame
    return pd.read_parquet(path, engine="pyarrow")
