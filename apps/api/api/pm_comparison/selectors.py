# =============================================================================
# 모듈: PM SPIDER 파일 셀렉터
# 주요 함수: iter_raw_files, iter_score_files, iter_decomp_files, collect_partition_options, read_parquet
# 주요 가정: data와 result는 PM_COMPARISON_DATA_ROOT 바로 아래에 위치합니다.
# =============================================================================
from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Iterable, Sequence

from django.conf import settings

import pandas as pd

RAW_DIR_NAME = "data"
SCORE_DIR_NAME = "result"
SCORE_DATA_DIR_NAME = "score_data"
DECOMP_DATA_DIR_NAME = "decomp_data"

RAW_PARTITION_KEYS = [
    "line_id",
    "eqp_id",
    "fdc_bin",
    "dt",
    "type",
    "ppid",
    "recipe_id",
    "data_source",
    "trace_param_name",
]

RAW_OPTION_DEPENDENCIES = {
    "line_id": [],
    "eqp_id": ["line_id"],
    "fdc_bin": ["line_id", "eqp_id"],
    "dt": ["line_id", "eqp_id", "fdc_bin"],
    "type": ["line_id", "eqp_id", "fdc_bin", "dt"],
    "ppid": ["line_id", "eqp_id", "fdc_bin", "dt", "type"],
    "recipe_id": ["line_id", "eqp_id", "fdc_bin", "dt", "type", "ppid"],
    "data_source": ["line_id", "eqp_id", "fdc_bin", "dt", "type", "ppid", "recipe_id"],
    "trace_param_name": ["line_id", "eqp_id", "fdc_bin", "dt", "type", "ppid", "recipe_id", "data_source"],
}

SCORE_PARTITION_KEYS = [
    "line_id",
    "eqp_id",
    "chamber_id",
    "type",
    "data_type",
]

SCORE_OPTION_DEPENDENCIES = {
    "line_id": [],
    "eqp_id": ["line_id"],
    "chamber_id": ["line_id", "eqp_id"],
    "type": ["line_id", "eqp_id", "chamber_id"],
    "data_type": ["line_id", "eqp_id", "chamber_id", "type"],
}

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
    """data 또는 result 데이터셋 루트를 반환합니다."""

    root = ensure_data_root() / dataset_name
    if not root.exists():
        raise FileNotFoundError(f"PM SPIDER {dataset_name} 경로를 찾을 수 없습니다: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"PM SPIDER {dataset_name} 경로가 폴더가 아닙니다: {root}")
    return root


def _existing_child_root(parent: Path, child_name: str) -> Path | None:
    """부모 디렉터리 아래 선택적 데이터셋 루트를 반환합니다."""

    root = parent / child_name
    if root.exists() and root.is_dir():
        return root
    return None


def _is_ignored_path(path: Path) -> bool:
    """Jupyter checkpoint 등 탐색 제외 경로인지 확인합니다."""

    return ".ipynb_checkpoints" in path.parts


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
    if _is_ignored_path(resolved):
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


def _plain_segment(value: str | None) -> str:
    """plain layout glob segment를 생성합니다."""

    return value or "*"


def _iter_plain_raw_files(
    root: Path,
    filters: dict[str, str | None],
    *,
    data_source: str,
    dt_candidates: Sequence[str | None],
    trace_candidates: Sequence[str | None],
    max_files: int,
) -> Iterable[Path]:
    """BASE_DATA/{LINE_ID}/{EQP_ID}/{CHAMBER_ID}/... plain layout 파일을 순회합니다."""

    line_id = _plain_segment(filters.get("line_id"))
    eqp_id = _plain_segment(filters.get("eqp_id"))
    chamber_id = _plain_segment(filters.get("fdc_bin"))
    type_segment = _segment("type", filters.get("type"))
    ppid_segment = _segment("ppid", filters.get("ppid"))
    recipe_segment = _segment("recipe_id", filters.get("recipe_id"))
    seen: set[Path] = set()

    source_dir = "trace" if data_source == "trace" else "oes" if data_source.startswith("oes") else data_source
    for dt_value in dt_candidates:
        dt_segment = _plain_segment(dt_value)
        if source_dir == "trace":
            for trace_value in trace_candidates:
                param_segment = _segment("trace_param_name", trace_value)
                pattern = (
                    f"{line_id}/{eqp_id}/{chamber_id}/{dt_segment}/trace/"
                    f"{type_segment}/{ppid_segment}/{recipe_segment}/priority=*/{param_segment}"
                )
                leaf_patterns = ["*.parquet", "*/*.parquet"]
                for leaf_pattern in leaf_patterns:
                    for path in root.glob(f"{pattern}/{leaf_pattern}"):
                        safe_path = _safe_relative_file(path, root)
                        if safe_path is None or safe_path in seen:
                            continue
                        seen.add(safe_path)
                        yield safe_path
                        if len(seen) >= max_files:
                            return
            continue

        if source_dir == "oes":
            pattern = (
                f"{line_id}/{eqp_id}/{chamber_id}/{dt_segment}/oes/"
                f"{_plain_segment(filters.get('type'))}/*/"
                f"{_plain_segment(filters.get('ppid'))}/{_plain_segment(filters.get('recipe_id'))}"
            )
            leaf_patterns = ["*/*/*.parquet", "*/*/*/*.parquet"]
            for leaf_pattern in leaf_patterns:
                for path in root.glob(f"{pattern}/{leaf_pattern}"):
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
    """data 아래에서 요청 조건에 맞는 Parquet 후보 파일을 순회합니다."""

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

    for dt_value in dt_candidates:
        filters["dt"] = dt_value
        for trace_value in trace_candidates:
            filters["trace_param_name"] = trace_value
            for path in _iter_partition_files(root, RAW_PARTITION_KEYS, filters, max_files=max_files):
                if path in seen:
                    continue
                seen.add(path)
                yield path
                if len(seen) >= max_files:
                    return

    for path in _iter_plain_raw_files(
        root,
        filters,
        data_source=data_source,
        dt_candidates=dt_candidates,
        trace_candidates=trace_candidates,
        max_files=max_files,
    ):
        if path in seen:
            continue
        seen.add(path)
        yield path
        if len(seen) >= max_files:
            return


def iter_score_files(selection: dict[str, object], *, data_type: str) -> Iterable[Path]:
    """result 아래에서 요청 조건에 맞는 Parquet 후보 파일을 순회합니다."""

    result_root = ensure_dataset_root(SCORE_DIR_NAME)
    score_data_root = _existing_child_root(result_root, SCORE_DATA_DIR_NAME)
    roots = [root for root in [score_data_root, result_root] if root is not None]
    filters = _partition_filters(selection, REQUEST_TO_SCORE_PARTITION)
    # fdcBin과 chamber_id는 동일하므로 chamberId 미지정 시 fdcBin으로 대체합니다.
    inferred_chamber_id = False
    if not filters.get("chamber_id"):
        fdc_bin = selection.get("fdcBin")
        if fdc_bin:
            filters["chamber_id"] = str(fdc_bin)
            inferred_chamber_id = True
    filters["data_type"] = data_type
    max_files = int(getattr(settings, "PM_COMPARISON_MAX_FILES", 400))
    seen: set[Path] = set()
    key_variants = [SCORE_PARTITION_KEYS]
    if not filters.get("chamber_id") or inferred_chamber_id:
        key_variants.append([key for key in SCORE_PARTITION_KEYS if key != "chamber_id"])
    for root in roots:
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
        result_root = ensure_dataset_root(SCORE_DIR_NAME)
    except (FileNotFoundError, NotADirectoryError):
        return
    root = _existing_child_root(result_root, DECOMP_DATA_DIR_NAME)
    if root is None:
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
            children = sorted(path for path in current.iterdir() if path.is_dir() and not _is_ignored_path(path))
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


def _meta_filters(selection: dict[str, object] | None) -> dict[str, str]:
    """메타 조회 선택값을 partition key 기준 필터로 변환합니다."""

    if not selection:
        return {}
    mapping = {
        "lineId": "line_id",
        "eqpId": "eqp_id",
        "fdcBin": "fdc_bin",
        "type": "type",
        "ppid": "ppid",
        "recipeId": "recipe_id",
        "traceDataSource": "data_source",
    }
    filters: dict[str, str] = {}
    for request_key, partition_key in mapping.items():
        value = selection.get(request_key)
        if value:
            filters[partition_key] = str(value)
    return filters


def _score_meta_filters(selection: dict[str, object] | None) -> dict[str, str]:
    """메타 조회 선택값을 score partition key 기준 필터로 변환합니다."""

    if not selection:
        return {}
    filters = _meta_filters(selection)
    score_filters: dict[str, str] = {}
    for raw_key, score_key in [("line_id", "line_id"), ("eqp_id", "eqp_id"), ("fdc_bin", "chamber_id"), ("type", "type")]:
        value = filters.get(raw_key)
        if value:
            score_filters[score_key] = value
    return score_filters


def _matches_dependencies(
    values: dict[str, str],
    filters: dict[str, str],
    dependencies_by_key: dict[str, list[str]],
    key: str,
) -> bool:
    """옵션 key보다 상위 선택값이 path 값과 일치하는지 확인합니다."""

    for dependency in dependencies_by_key.get(key, []):
        expected = filters.get(dependency)
        if expected and values.get(dependency) != expected:
            return False
    return True


def _should_descend_for_key(filters: dict[str, str], key: str, value: str) -> bool:
    """선택된 partition 값과 일치할 때만 하위 단계로 내려갑니다."""

    expected = filters.get(key)
    if expected:
        return expected == value
    return bool(filters.get("fdc_bin") and key in {"dt", "type", "ppid", "recipe_id", "data_source"})


def _scan_hive_raw_dirs(root: Path, max_dirs: int, filters: dict[str, str]) -> dict[str, set[str]]:
    """key=value raw layout에서 cascade 옵션을 수집합니다."""

    options: dict[str, set[str]] = {key: set() for key in RAW_PARTITION_KEYS}
    queue: deque[tuple[Path, int, dict[str, str]]] = deque([(root, 0, {})])
    visited = 0
    while queue and visited < max_dirs:
        current, depth, parent_values = queue.popleft()
        if depth >= len(RAW_PARTITION_KEYS):
            continue
        expected_key = RAW_PARTITION_KEYS[depth]
        try:
            children = sorted(path for path in current.iterdir() if path.is_dir() and not _is_ignored_path(path))
        except OSError:
            continue
        visited += len(children)
        for child in children:
            child_values = parse_partition_values(child)
            value = child_values.get(expected_key)
            if not value:
                continue
            partition = {**parent_values, expected_key: value}
            if _matches_dependencies(partition, filters, RAW_OPTION_DEPENDENCIES, expected_key):
                options[expected_key].add(value)
            if _should_descend_for_key(filters, expected_key, value):
                queue.append((child, depth + 1, partition))
            if visited >= max_dirs:
                break
    return options


def _scan_plain_raw_dirs(root: Path, max_dirs: int, filters: dict[str, str]) -> dict[str, set[str]]:
    """plain raw layout에서 주요 선택값을 수집합니다."""

    options: dict[str, set[str]] = {key: set() for key in RAW_PARTITION_KEYS}
    visited = 0
    try:
        line_dirs = sorted(path for path in root.iterdir() if path.is_dir() and not _is_ignored_path(path))
    except OSError:
        return options

    for line_dir in line_dirs:
        if "=" in line_dir.name:
            continue
        options["line_id"].add(line_dir.name)
        if not _should_descend_for_key(filters, "line_id", line_dir.name):
            continue
        visited += 1
        if visited >= max_dirs:
            break
        try:
            eqp_dirs = sorted(path for path in line_dir.iterdir() if path.is_dir() and not _is_ignored_path(path))
        except OSError:
            continue
        for eqp_dir in eqp_dirs:
            options["eqp_id"].add(eqp_dir.name)
            if not _should_descend_for_key(filters, "eqp_id", eqp_dir.name):
                continue
            visited += 1
            if visited >= max_dirs:
                break
            try:
                chamber_dirs = sorted(path for path in eqp_dir.iterdir() if path.is_dir() and not _is_ignored_path(path))
            except OSError:
                continue
            for chamber_dir in chamber_dirs:
                options["fdc_bin"].add(chamber_dir.name)
                if not _should_descend_for_key(filters, "fdc_bin", chamber_dir.name):
                    continue
                visited += 1
                if visited >= max_dirs:
                    break
                try:
                    dt_dirs = sorted(path for path in chamber_dir.iterdir() if path.is_dir() and not _is_ignored_path(path))
                except OSError:
                    continue
                for dt_dir in dt_dirs:
                    options["dt"].add(dt_dir.name)
                    if not _should_descend_for_key(filters, "dt", dt_dir.name):
                        continue
                    visited += 1
                    if visited >= max_dirs:
                        break
                    for source_name in ("trace", "oes"):
                        source_root = dt_dir / source_name
                        if source_root.is_dir():
                            options["data_source"].add(source_name)
                    trace_root = dt_dir / "trace"
                    if trace_root.is_dir():
                        base_values = {
                            "line_id": line_dir.name,
                            "eqp_id": eqp_dir.name,
                            "fdc_bin": chamber_dir.name,
                            "dt": dt_dir.name,
                            "data_source": "trace",
                        }
                        try:
                            trace_dirs = sorted(
                                path for path in trace_root.rglob("*") if path.is_dir() and not _is_ignored_path(path)
                            )
                        except OSError:
                            trace_dirs = []
                        for trace_dir in trace_dirs:
                            visited += 1
                            partition = {**base_values, **parse_partition_values(trace_dir)}
                            for key in ("type", "ppid", "recipe_id", "trace_param_name"):
                                value = partition.get(key)
                                if value and _matches_dependencies(partition, filters, RAW_OPTION_DEPENDENCIES, key):
                                    options[key].add(value)
                            if visited >= max_dirs:
                                break
        if visited >= max_dirs:
            break

    return options


def _scan_score_dirs(root: Path, max_dirs: int, filters: dict[str, str]) -> dict[str, set[str]]:
    """score layout에서 cascade 옵션을 수집합니다."""

    options: dict[str, set[str]] = {key: set() for key in SCORE_PARTITION_KEYS}
    queue: deque[tuple[Path, int, dict[str, str]]] = deque([(root, 0, {})])
    visited = 0
    while queue and visited < max_dirs:
        current, depth, parent_values = queue.popleft()
        if depth >= len(SCORE_PARTITION_KEYS):
            continue
        expected_key = SCORE_PARTITION_KEYS[depth]
        try:
            children = sorted(path for path in current.iterdir() if path.is_dir() and not _is_ignored_path(path))
        except OSError:
            continue
        visited += len(children)
        for child in children:
            child_values = parse_partition_values(child)
            value = child_values.get(expected_key)
            if not value:
                continue
            partition = {**parent_values, expected_key: value}
            if _matches_dependencies(partition, filters, SCORE_OPTION_DEPENDENCIES, expected_key):
                options[expected_key].add(value)
            if _should_descend_for_key(filters, expected_key, value):
                queue.append((child, depth + 1, partition))
            if visited >= max_dirs:
                break
    return options


def collect_partition_options(selection: dict[str, object] | None = None) -> dict[str, list[str]]:
    """data 아래 partition 값을 수집하고 없으면 result score partition 값으로 대체합니다."""

    max_dirs = int(getattr(settings, "PM_COMPARISON_MAX_META_DIRS", 5000))
    filters = _meta_filters(selection)
    try:
        raw_root = ensure_dataset_root(RAW_DIR_NAME)
        options = _scan_hive_raw_dirs(raw_root, max_dirs, filters)
        plain_options = _scan_plain_raw_dirs(raw_root, max_dirs, filters)
        for key, values in plain_options.items():
            options.setdefault(key, set()).update(values)
    except (FileNotFoundError, NotADirectoryError):
        # data가 없으면 result/score_data 또는 result partition 값으로 대체합니다.
        options = {key: set() for key in RAW_PARTITION_KEYS}
        try:
            result_root = ensure_dataset_root(SCORE_DIR_NAME)
            score_root = _existing_child_root(result_root, SCORE_DATA_DIR_NAME) or result_root
            score_opts = _scan_score_dirs(score_root, max_dirs, _score_meta_filters(selection))
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
