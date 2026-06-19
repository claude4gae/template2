# =============================================================================
# 모듈: PM SPIDER 서비스
# 주요 함수: get_meta, compare_pm_window
# 주요 가정: data는 원본, result는 PM 주기별 scoring 결과입니다.
# =============================================================================
from __future__ import annotations

import math
from bisect import bisect_right
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from api.pm_comparison import selectors

DATE_COLUMN = "날짜"

TRACE_COLUMNS = [
    "line_id",
    "eqp_id",
    "fdc_bin",
    "type",
    "ppid",
    "recipe_id",
    "trace_param_name",
    DATE_COLUMN,
    "root_lot_id",
    "lot_id",
    "wafer_id",
    "time",
    "step_time",
    "value",
    "ch_step",
    "slot_no",
    "group",
]

OES_ID_COLUMNS = [
    "line_id",
    "device_id",
    "ppid",
    "recipe_id",
    "step_seq",
    "eqp_id",
    "bin_id",
    "lot_id",
    "slot_id",
    DATE_COLUMN,
    "wafer_end_time",
    "rcp_step",
    "name",
    "Time",
    "wavelength",
    "value",
]

SCORE_COLUMNS = [
    "line_id",
    "eqp_id",
    "chamber_id",
    DATE_COLUMN,
    "type",
    "data_type",
    "item_name",
    "step",
    "wavelength",
    "score",
    # trace 전용 변화량 컬럼입니다.
    "delta_shape",
    "delta_jitter",
    "delta_level",
    "flag",
    "alarm_pct",
    # OES 전용 변화량 컬럼입니다.
    "delta_spectrum",
    "direction",
    "flagged_wl",
]
SCORE_FRAME_COLUMNS = [*SCORE_COLUMNS, "pm_date"]


class PmComparisonServiceError(Exception):
    """PM SPIDER 서비스 오류를 HTTP 상태와 함께 표현합니다."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        """오류 메시지와 상태 코드를 저장합니다."""

        super().__init__(message)
        self.status_code = status_code


def _json_safe_value(value: Any) -> Any:
    """JSON 직렬화 가능한 값으로 정리합니다."""

    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        return _json_safe_value(value.item())
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _snake_to_camel(value: str) -> str:
    """snake_case 문자열을 camelCase로 변환합니다."""

    parts = value.split("_")
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def _camelize_mapping(row: dict[str, Any]) -> dict[str, Any]:
    """dict 키를 camelCase로 변환하고 값을 JSON 안전 형태로 바꿉니다."""

    return {_snake_to_camel(key): _json_safe_value(value) for key, value in row.items()}


def _selection_int(selection: dict[str, object], key: str, default: int, minimum: int, maximum: int) -> int:
    """요청 정수 옵션을 안전한 범위로 정규화합니다."""

    try:
        value = int(selection.get(key) or default)
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def _selection_float(selection: dict[str, object], key: str) -> float | None:
    """요청 실수 옵션을 반환합니다."""

    try:
        value = selection.get(key)
        if value in (None, ""):
            return None
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


def _compat_row_limit(selection: dict[str, object]) -> int:
    """기존 행 목록 호환 응답의 최대 행 수를 반환합니다."""

    return _selection_int(selection, "limit", 1200, 50, 5000)


def _chart_max_points(selection: dict[str, object]) -> int:
    """series 하나당 차트에 내려줄 최대 점 수를 반환합니다."""

    return _selection_int(selection, "maxPoints", 2400, 100, 20000)


def _apply_numeric_x_range(frame: pd.DataFrame, x_column: str, selection: dict[str, object]) -> pd.DataFrame:
    """요청 X 범위가 있으면 frame을 좁힙니다."""

    start = _selection_float(selection, "xStart")
    end = _selection_float(selection, "xEnd")
    if start is None and end is None:
        return frame
    ranged = frame
    if start is not None:
        ranged = ranged[ranged[x_column] >= start]
    if end is not None:
        ranged = ranged[ranged[x_column] <= end]
    return ranged.copy()


def _downsample_xy(points: list[tuple[float, float]], max_points: int) -> list[tuple[float, float]]:
    """최소/최대 bucket 방식으로 spike를 보존하며 점 수를 줄입니다."""

    clean_points = [(x, y) for x, y in points if math.isfinite(x) and math.isfinite(y)]
    clean_points.sort(key=lambda point: point[0])
    count = len(clean_points)
    if count <= max_points:
        return clean_points
    bucket_count = max(1, max_points // 2)
    bucket_size = max(1, math.ceil(count / bucket_count))
    sampled: list[tuple[float, float]] = []
    for start in range(0, count, bucket_size):
        bucket = clean_points[start : start + bucket_size]
        if not bucket:
            continue
        low = min(bucket, key=lambda point: point[1])
        high = max(bucket, key=lambda point: point[1])
        if low[0] <= high[0]:
            sampled.extend([low, high] if low != high else [low])
        else:
            sampled.extend([high, low] if low != high else [low])
    sampled.sort(key=lambda point: point[0])
    if len(sampled) > max_points:
        step = len(sampled) / max_points
        sampled = [sampled[int(index * step)] for index in range(max_points)]
    return sampled


def _line_chart_payload(
    frame: pd.DataFrame,
    *,
    x_column: str,
    y_column: str,
    selection: dict[str, object],
    series_columns: list[str],
    label_columns: list[str] | None = None,
) -> dict[str, Any]:
    """Canvas 라인 차트용 컬럼 기반 응답을 생성합니다."""

    empty = {
        "series": [],
        "xDomain": [None, None],
        "yDomain": [None, None],
        "sourcePointCount": 0,
        "pointCount": 0,
        "downsampled": False,
        "maxPoints": _chart_max_points(selection),
    }
    if frame.empty or x_column not in frame.columns or y_column not in frame.columns:
        return empty

    work = frame.copy()
    work[x_column] = pd.to_numeric(work[x_column], errors="coerce")
    work[y_column] = pd.to_numeric(work[y_column], errors="coerce")
    work = work[work[x_column].notna() & work[y_column].notna()].copy()
    if work.empty:
        return empty
    work = _apply_numeric_x_range(work, x_column, selection)
    if work.empty:
        return empty

    max_points = _chart_max_points(selection)
    if not series_columns:
        work["_series"] = "series"
        series_columns = ["_series"]
    labels = label_columns or series_columns
    series_payload: list[dict[str, Any]] = []
    source_count = 0
    point_count = 0
    x_values: list[float] = []
    y_values: list[float] = []
    groupby: str | list[str] = series_columns[0] if len(series_columns) == 1 else series_columns
    for group_key, group in work.groupby(groupby, dropna=False, sort=True):
        group_values = group_key if isinstance(group_key, tuple) else (group_key,)
        label_parts = [str(value) for value in group_values if value not in (None, "")]
        points = [
            (float(row[x_column]), float(row[y_column]))
            for row in group[[x_column, y_column]].to_dict(orient="records")
        ]
        source_count += len(points)
        sampled = _downsample_xy(points, max_points)
        if not sampled:
            continue
        xs = [round(point[0], 6) for point in sampled]
        ys = [_json_safe_value(round(point[1], 6)) for point in sampled]
        x_values.extend(xs)
        y_values.extend(float(value) for value in ys if value is not None)
        point_count += len(sampled)
        meta = {}
        for column, value in zip(series_columns, group_values):
            meta[_snake_to_camel(column)] = _json_safe_value(value)
        label = " · ".join(label_parts) if label_parts else "series"
        if labels:
            first_row = group.iloc[0].to_dict()
            label_values = [str(first_row.get(column)) for column in labels if first_row.get(column) not in (None, "")]
            if label_values:
                label = " · ".join(label_values)
        series_payload.append(
            {
                "key": "|".join(label_parts) or f"series-{len(series_payload) + 1}",
                "label": label,
                "x": xs,
                "y": ys,
                "meta": meta,
                "sourcePointCount": len(points),
                "pointCount": len(sampled),
                "downsampled": len(sampled) < len(points),
            }
        )

    if not series_payload:
        return empty
    return {
        "series": series_payload,
        "xDomain": [min(x_values), max(x_values)] if x_values else [None, None],
        "yDomain": [min(y_values), max(y_values)] if y_values else [None, None],
        "sourcePointCount": source_count,
        "pointCount": point_count,
        "downsampled": point_count < source_count,
        "maxPoints": max_points,
    }


def _trace_chart_x_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """trace frame에 차트용 숫자 X 컬럼을 추가합니다."""

    work = frame.copy()
    if "step_time" in work.columns:
        work["chart_x"] = pd.to_numeric(work["step_time"], errors="coerce")
    elif "period" in work.columns:
        work["chart_x"] = pd.to_numeric(work["period"], errors="coerce")
    elif "time" in work.columns:
        time_values = pd.to_datetime(work["time"], errors="coerce", utc=True)
        if time_values.notna().any():
            origin = time_values.dropna().min()
            work["chart_x"] = (time_values - origin).dt.total_seconds()
        else:
            work["chart_x"] = None
    else:
        work["chart_x"] = work.groupby(["cycle_index", "phase"], dropna=False).cumcount()
    if work["chart_x"].isna().all():
        work["chart_x"] = work.groupby(["cycle_index", "phase"], dropna=False).cumcount()
    return work, "chart_x"


def _trace_series_columns(frame: pd.DataFrame) -> list[str]:
    """trace 라인 차트 series 그룹 기준 컬럼을 선택합니다."""

    candidates = ["phase", "cycle_index", "trace_param_name", "ch_step", "lot_id", "slot_no", "wafer_id"]
    return [column for column in candidates if column in frame.columns]


def _heatmap_bins(selection: dict[str, object]) -> tuple[int, int]:
    """OES 히트맵 해상도를 요청 옵션에서 얻습니다."""

    x_bins = _selection_int(selection, "heatmapXBins", 1200, 20, 1600)
    y_bins = _selection_int(selection, "heatmapYBins", 100, 10, 240)
    return x_bins, y_bins


def _bin_edges(min_value: float, max_value: float, bins: int) -> list[float]:
    """균등 bin edge를 생성합니다."""

    if not math.isfinite(min_value) or not math.isfinite(max_value):
        return []
    if min_value == max_value:
        return [min_value, max_value + 1]
    step = (max_value - min_value) / bins
    return [min_value + step * index for index in range(bins + 1)]


def _value_edges(values: list[float]) -> list[float]:
    """실제 측정값을 중심으로 하는 bin edge를 생성합니다."""

    if not values:
        return []
    if len(values) == 1:
        value = values[0]
        margin = max(abs(value) * 1e-9, 0.5)
        return [value - margin, value + margin]
    edges = [values[0] - (values[1] - values[0]) / 2]
    edges.extend((values[index] + values[index + 1]) / 2 for index in range(len(values) - 1))
    edges.append(values[-1] + (values[-1] - values[-2]) / 2)
    return edges


def _bin_centers(edges: list[float]) -> list[float]:
    """bin edge에서 center 값을 생성합니다."""

    return [round((edges[index] + edges[index + 1]) / 2, 6) for index in range(len(edges) - 1)]


def _nearest_value(values: list[float], target: float) -> float | None:
    """정렬된 실제 값 목록에서 target에 가장 가까운 값을 반환합니다."""

    if not values:
        return None
    right = bisect_right(values, target)
    if right <= 0:
        return values[0]
    if right >= len(values):
        return values[-1]
    left_value = values[right - 1]
    right_value = values[right]
    return left_value if abs(target - left_value) <= abs(right_value - target) else right_value


def _representative_values_for_edges(values: list[float], edges: list[float]) -> list[float]:
    """각 bin을 대표하는 실제 측정값을 반환합니다."""

    labels: list[float] = []
    cursor = 0
    last_index = len(edges) - 2
    for edge_index in range(max(0, len(edges) - 1)):
        start = edges[edge_index]
        end = edges[edge_index + 1]
        while cursor < len(values) and values[cursor] < start:
            cursor += 1
        next_cursor = cursor
        while next_cursor < len(values) and (
            values[next_cursor] < end or (edge_index == last_index and values[next_cursor] <= end)
        ):
            next_cursor += 1
        bucket = values[cursor:next_cursor]
        if bucket:
            labels.append(bucket[len(bucket) // 2])
        else:
            center = (start + end) / 2
            nearest = _nearest_value(values, center)
            labels.append(nearest if nearest is not None else center)
        cursor = max(cursor, next_cursor)
    return [round(value, 6) for value in labels]


def _bin_index(value: float, edges: list[float]) -> int | None:
    """값이 속한 bin index를 반환합니다."""

    if not edges or not math.isfinite(value):
        return None
    if value < edges[0] or value > edges[-1]:
        return None
    if value == edges[-1]:
        return len(edges) - 2
    return max(0, min(len(edges) - 2, bisect_right(edges, value) - 1))


def _flat_average_grid(
    frame: pd.DataFrame,
    *,
    x_edges: list[float],
    y_edges: list[float],
    value_column: str,
) -> list[float | None]:
    """평균값 1차원 matrix를 생성합니다."""

    width = max(0, len(x_edges) - 1)
    height = max(0, len(y_edges) - 1)
    sums = [0.0 for _ in range(width * height)]
    counts = [0 for _ in range(width * height)]
    for row in frame[["chart_x", "chart_y", value_column]].to_dict(orient="records"):
        x_index = _bin_index(float(row["chart_x"]), x_edges)
        y_index = _bin_index(float(row["chart_y"]), y_edges)
        value = row[value_column]
        if x_index is None or y_index is None or value is None or not math.isfinite(float(value)):
            continue
        offset = y_index * width + x_index
        sums[offset] += float(value)
        counts[offset] += 1
    return [round(sums[index] / counts[index], 6) if counts[index] else None for index in range(width * height)]


def _oes_heatmap_payload(frame: pd.DataFrame, selection: dict[str, object]) -> dict[str, Any]:
    """OES step frame에서 Canvas 히트맵 matrix를 생성합니다."""

    empty = {"width": 0, "height": 0, "wavelengths": [], "phases": [], "ref": [], "comp": [], "oob": []}
    if frame.empty or "wavelength" not in frame.columns or "value" not in frame.columns:
        return empty
    work = frame.copy()
    work["chart_x"] = pd.to_numeric(work["wavelength"], errors="coerce")
    if "traj_phase" in work.columns:
        work["chart_y"] = pd.to_numeric(work["traj_phase"], errors="coerce")
    else:
        work["chart_y"] = work.groupby(["phase", "cycle_index"], dropna=False).cumcount()
    work["value"] = pd.to_numeric(work["value"], errors="coerce")
    work = work[work["chart_x"].notna() & work["chart_y"].notna() & work["value"].notna()].copy()
    if work.empty:
        return empty
    x_bins, y_bins = _heatmap_bins(selection)
    x_values = sorted(float(value) for value in work["chart_x"].dropna().unique().tolist())
    if len(x_values) <= x_bins:
        x_edges = _value_edges(x_values)
        wavelength_labels = [round(value, 6) for value in x_values]
    else:
        x_edges = _bin_edges(float(work["chart_x"].min()), float(work["chart_x"].max()), x_bins)
        wavelength_labels = _representative_values_for_edges(x_values, x_edges)
    y_edges = _bin_edges(float(work["chart_y"].min()), float(work["chart_y"].max()), min(y_bins, max(1, int(work["chart_y"].nunique()) or y_bins)))
    if len(x_edges) < 2 or len(y_edges) < 2:
        return empty
    ref_frame = work[work.get("phase", pd.Series(dtype=str)).astype(str) == "ref"]
    comp_frame = work[work.get("phase", pd.Series(dtype=str)).astype(str) != "ref"]
    ref_values = _flat_average_grid(ref_frame, x_edges=x_edges, y_edges=y_edges, value_column="value")
    comp_values = _flat_average_grid(comp_frame, x_edges=x_edges, y_edges=y_edges, value_column="value")
    oob_values: list[float | None] = []
    for ref_value, comp_value in zip(ref_values, comp_values):
        oob_values.append(
            round(comp_value - ref_value, 6)
            if ref_value is not None and comp_value is not None
            else None
        )
    width = len(x_edges) - 1
    height = len(y_edges) - 1
    return {
        "width": width,
        "height": height,
        "wavelengths": wavelength_labels,
        "phases": _bin_centers(y_edges),
        "ref": ref_values,
        "comp": comp_values,
        "oob": oob_values,
        "sourcePointCount": int(len(work)),
    }


def _oes_spectrum_payload(frame: pd.DataFrame, selection: dict[str, object]) -> dict[str, Any]:
    """OES step frame에서 wavelength별 ref/comp median 차트를 생성합니다."""

    if frame.empty or "wavelength" not in frame.columns or "value" not in frame.columns:
        return {"series": [], "xDomain": [None, None], "yDomain": [None, None], "sourcePointCount": 0, "pointCount": 0}
    work = frame.copy()
    work["wavelength"] = pd.to_numeric(work["wavelength"], errors="coerce")
    work["value"] = pd.to_numeric(work["value"], errors="coerce")
    work = work[work["wavelength"].notna() & work["value"].notna()].copy()
    if work.empty:
        return {"series": [], "xDomain": [None, None], "yDomain": [None, None], "sourcePointCount": 0, "pointCount": 0}
    work["series_phase"] = work.get("phase", pd.Series(["comp"] * len(work))).astype(str).map(lambda value: "ref" if value == "ref" else "comp")
    grouped = work.groupby(["series_phase", "wavelength"], dropna=False)["value"].median().reset_index()
    return _line_chart_payload(
        grouped,
        x_column="wavelength",
        y_column="value",
        selection=selection,
        series_columns=["series_phase"],
        label_columns=["series_phase"],
    )


def _date_key(value: Any) -> str:
    """PM 날짜 값을 비교 가능한 YYYY-MM-DD 문자열로 정규화합니다."""

    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_convert("UTC").tz_localize(None)
    return timestamp.date().isoformat()


def _selected_pm_date(selection: dict[str, object]) -> str:
    """요청에서 현재 PM 날짜를 추출합니다."""

    return _date_key(selection["pmTimestamp"])


def _apply_partitions(frame: pd.DataFrame, path: Path) -> pd.DataFrame:
    """파일 경로 partition 값을 누락 컬럼에 보강합니다."""

    partitions = selectors.parse_partition_values(path)
    for key, value in partitions.items():
        if key not in frame.columns:
            frame[key] = value
    return frame


def _read_frames(
    files: Iterable[Path],
    *,
    columns: list[str] | None,
    warnings: list[str],
) -> tuple[list[pd.DataFrame], int]:
    """후보 파일을 DataFrame 목록으로 읽습니다."""

    frames: list[pd.DataFrame] = []
    file_count = 0
    for path in files:
        file_count += 1
        try:
            frame = selectors.read_parquet(path, columns)
            frames.append(_apply_partitions(frame, path))
        except Exception as exc:
            warnings.append(f"읽기 실패: {path.name} ({exc})")
    return frames, file_count


def _normalize_score_frame(frame: pd.DataFrame, selection: dict[str, object], data_type: str) -> pd.DataFrame:
    """result frame을 표준 컬럼과 요청 조건으로 정리합니다."""

    if frame.empty:
        return pd.DataFrame(columns=SCORE_FRAME_COLUMNS)
    for column in SCORE_COLUMNS:
        if column not in frame.columns:
            frame[column] = None
    frame = frame.copy()
    frame["line_id"] = frame["line_id"].fillna(selection.get("lineId"))
    frame["eqp_id"] = frame["eqp_id"].fillna(selection.get("eqpId"))
    chamber_id = str(selection.get("chamberId") or selection.get("fdcBin") or "")
    frame["chamber_id"] = frame["chamber_id"].fillna(chamber_id)
    frame["type"] = frame["type"].fillna(selection.get("type"))
    frame["data_type"] = frame["data_type"].fillna(data_type)
    mask = (
        (frame["line_id"].astype(str) == str(selection.get("lineId")))
        & (frame["eqp_id"].astype(str) == str(selection.get("eqpId")))
        & (frame["type"].astype(str) == str(selection.get("type")))
        & (frame["data_type"].astype(str) == data_type)
    )
    if chamber_id:
        mask = mask & (frame["chamber_id"].astype(str) == chamber_id)
    frame = frame[mask].copy()
    if DATE_COLUMN not in frame.columns or "score" not in frame.columns:
        return frame.iloc[0:0].copy()
    frame["pm_date"] = frame[DATE_COLUMN].map(_date_key)
    frame["score"] = pd.to_numeric(frame["score"], errors="coerce")
    return frame[frame["score"].notna()].copy()


def _read_score(selection: dict[str, object], data_type: str, warnings: list[str]) -> tuple[pd.DataFrame, int]:
    """result를 읽어 표준 frame으로 반환합니다."""

    files = selectors.iter_score_files(selection, data_type=data_type)
    frames, file_count = _read_frames(files, columns=SCORE_COLUMNS, warnings=warnings)
    if not frames:
        return pd.DataFrame(columns=SCORE_FRAME_COLUMNS), file_count
    frame = _normalize_score_frame(pd.concat(frames, ignore_index=True), selection, data_type)
    return frame, file_count


def _cycle_map(score_frame: pd.DataFrame, current_pm_date: str) -> dict[str, int]:
    """현재 PM 날짜 기준 상대 cycle index를 계산합니다."""

    dates = sorted(
        date
        for date in score_frame.get("pm_date", pd.Series(dtype=str)).dropna().unique().tolist()
        if str(date) <= current_pm_date
    )
    if current_pm_date not in dates:
        dates.append(current_pm_date)
        dates = sorted(set(dates))
    previous_dates = [date for date in dates if date < current_pm_date]
    mapping = {current_pm_date: 0}
    for offset, date in enumerate(reversed(previous_dates), start=1):
        mapping[date] = -offset
    return mapping


def _requested_ref_dates(selection: dict[str, object]) -> set[str] | None:
    """요청된 ref PM 날짜 목록을 정규화합니다."""

    if "refPmDates" not in selection:
        return None
    dates: set[str] = set()
    for value in selection.get("refPmDates") or []:
        try:
            dates.add(_date_key(value))
        except (TypeError, ValueError):
            continue
    return dates


def _selected_ref_dates(selection: dict[str, object], cycle_map: dict[str, int]) -> set[str]:
    """선택된 ref PM 날짜를 cycle map 기준으로 확정합니다."""

    available = {date for date, cycle_index in cycle_map.items() if cycle_index < 0}
    requested = _requested_ref_dates(selection)
    if requested is None:
        return available
    return available.intersection(requested)


def _selection_with_raw_dt_values(
    selection: dict[str, object],
    current_pm_date: str,
    selected_ref_dates: set[str],
) -> dict[str, object]:
    """raw 파일 탐색이 선택된 PM cycle 날짜로 좁혀지도록 dt 후보를 보강합니다."""

    dt_values: list[str] = []
    for value in selection.get("dtValues") or []:
        dt_values.extend(selectors.date_partition_candidates(value))
    for value in [current_pm_date, *sorted(selected_ref_dates)]:
        dt_values.extend(selectors.date_partition_candidates(value))
    if not dt_values:
        dt_values.extend(selectors.date_partition_candidates(selection.get("pmTimestamp")))
    return {
        **selection,
        "dtValues": list(dict.fromkeys(dt_values)),
    }


def _ref_cycle_rows(cycle_map: dict[str, int], selected_ref_dates: set[str]) -> list[dict[str, Any]]:
    """화면 checkbox에 표시할 ref cycle 목록을 생성합니다."""

    rows = [
        {
            "pm_date": date,
            "cycle_index": cycle_index,
            "phase": "ref",
            "selected": date in selected_ref_dates,
        }
        for date, cycle_index in cycle_map.items()
        if cycle_index < 0
    ]
    rows.sort(key=lambda row: int(row["cycle_index"]), reverse=True)
    return [_camelize_mapping(row) for row in rows]


def _filter_selected_cycles(frame: pd.DataFrame, selected_ref_dates: set[str]) -> pd.DataFrame:
    """comp와 선택된 ref cycle만 남깁니다."""

    if frame.empty or "cycle_index" not in frame.columns or "pm_date" not in frame.columns:
        return frame
    return frame[(frame["cycle_index"] == 0) | (frame["pm_date"].isin(selected_ref_dates))].copy()


def _add_cycle_columns(frame: pd.DataFrame, cycle_map: dict[str, int]) -> pd.DataFrame:
    """frame에 cycle_index와 ref/comp phase를 추가합니다."""

    if frame.empty:
        frame = frame.copy()
        frame["cycle_index"] = []
        frame["phase"] = []
        return frame
    frame = frame.copy()
    if "pm_date" not in frame.columns:
        frame["pm_date"] = frame[DATE_COLUMN].map(_date_key)
    frame["cycle_index"] = frame["pm_date"].map(cycle_map)
    frame = frame[frame["cycle_index"].notna()].copy()
    frame["cycle_index"] = frame["cycle_index"].astype(int)
    frame["phase"] = frame["cycle_index"].map(lambda value: "comp" if value == 0 else "ref")
    return frame


def _score_trend_rows(
    score_frame: pd.DataFrame,
    cycle_map: dict[str, int],
    selected_ref_dates: set[str],
) -> list[dict[str, Any]]:
    """PM cycle별 score scatter row를 생성합니다."""

    frame = _filter_selected_cycles(_add_cycle_columns(score_frame, cycle_map), selected_ref_dates)
    if frame.empty:
        return []
    frame = frame.sort_values(["cycle_index", "score", "item_name", "step", "wavelength"])
    columns = ["pm_date", "cycle_index", "phase", "item_name", "step", "wavelength", "score"]
    return [_camelize_mapping(row) for row in frame[columns].to_dict(orient="records")]


def _cycle_summary(
    score_frame: pd.DataFrame,
    cycle_map: dict[str, int],
    selected_ref_dates: set[str],
) -> list[dict[str, Any]]:
    """cycle별 포함 데이터 수와 worst score를 요약합니다."""

    frame = _filter_selected_cycles(_add_cycle_columns(score_frame, cycle_map), selected_ref_dates)
    if frame.empty:
        return []
    grouped = (
        frame.groupby(["pm_date", "cycle_index", "phase"], dropna=False)["score"]
        .agg(item_count="count", worst_score="min", avg_score="mean")
        .reset_index()
        .sort_values("cycle_index")
    )
    return [_camelize_mapping(row) for row in grouped.to_dict(orient="records")]


def _trace_rank_rows(score_frame: pd.DataFrame, current_pm_date: str) -> list[dict[str, Any]]:
    """trace score row를 rank row로 변환합니다."""

    if score_frame.empty or "pm_date" not in score_frame.columns:
        return []
    current = score_frame[score_frame["pm_date"] == current_pm_date].copy()
    current = current.sort_values(["score", "item_name"])
    rows = []
    for row in current.to_dict(orient="records"):
        rows.append(
            {
                "trace_sensor": row.get("item_name"),
                "item_name": row.get("item_name"),
                "step": row.get("step"),
                "score": row.get("score"),
                "delta_shape": row.get("delta_shape"),
                "delta_jitter": row.get("delta_jitter"),
                "delta_level": row.get("delta_level"),
                "flag": row.get("flag"),
                "alarm_pct": row.get("alarm_pct"),
                "pm_date": row.get("pm_date"),
                "cycle_index": 0,
                "phase": "comp",
            }
        )
    return [_camelize_mapping(row) for row in rows]


def _oes_rank_rows(score_frame: pd.DataFrame, current_pm_date: str) -> list[dict[str, Any]]:
    """OES score row를 rank row로 변환합니다."""

    if score_frame.empty or "pm_date" not in score_frame.columns:
        return []
    current = score_frame[score_frame["pm_date"] == current_pm_date].copy()
    current = current.sort_values(["score", "step", "wavelength", "item_name"])
    rows = []
    for row in current.to_dict(orient="records"):
        rows.append(
            {
                "item_name": row.get("item_name"),
                "step": row.get("step"),
                "wavelength": row.get("wavelength"),
                "score": row.get("score"),
                "delta_spectrum": row.get("delta_spectrum"),
                "direction": row.get("direction"),
                "flagged_wl": row.get("flagged_wl"),
                "pm_date": row.get("pm_date"),
                "cycle_index": 0,
                "phase": "comp",
            }
        )
    return [_camelize_mapping(row) for row in rows]


def _raw_cycle_frame(frame: pd.DataFrame, cycle_map: dict[str, int]) -> pd.DataFrame:
    """raw frame에 날짜 기반 cycle 정보를 추가합니다."""

    if frame.empty or DATE_COLUMN not in frame.columns:
        return frame.iloc[0:0].copy()
    frame = frame.copy()
    frame["pm_date"] = frame[DATE_COLUMN].map(_date_key)
    return _add_cycle_columns(frame, cycle_map)


def _prepare_trace(selection: dict[str, object], current_pm_date: str, warnings: list[str]) -> dict[str, Any]:
    """result 기반 trace rank와 data 기반 상세 trend를 준비합니다."""

    score_frame, score_file_count = _read_score(selection, "trace", warnings)
    cycle_map = _cycle_map(score_frame, current_pm_date)
    selected_ref_dates = _selected_ref_dates(selection, cycle_map)
    rank_rows = _trace_rank_rows(score_frame, current_pm_date)
    selected_sensors = [str(value) for value in selection.get("traceParamNames", []) if value]
    if not selected_sensors:
        selected_sensors = [row["traceSensor"] for row in rank_rows[:1] if row.get("traceSensor")]

    trend_rows: list[dict[str, Any]] = []
    shape_rows: list[dict[str, Any]] = []
    jitter_rows: list[dict[str, Any]] = []
    line_chart: dict[str, Any] = {"series": [], "xDomain": [None, None], "yDomain": [None, None]}
    raw_file_count = 0
    row_count = 0
    if selection.get("includeDetails", True):
        raw_selection = _selection_with_raw_dt_values(selection, current_pm_date, selected_ref_dates)
        files = selectors.iter_raw_files(
            raw_selection,
            data_source=str(selection.get("traceDataSource") or "trace"),
            trace_param_names=selected_sensors,
        )
        frames, raw_file_count = _read_frames(files, columns=TRACE_COLUMNS, warnings=warnings)
        if frames:
            frame = pd.concat(frames, ignore_index=True)
            if "trace_param_name" not in frame.columns and "name" in frame.columns:
                frame["trace_param_name"] = frame["name"]
            x_col = "time" if "time" in frame.columns else ("step_time" if "step_time" in frame.columns else None)
            if x_col and {"value", DATE_COLUMN, "trace_param_name"}.issubset(frame.columns):
                frame = _filter_selected_cycles(_raw_cycle_frame(frame, cycle_map), selected_ref_dates)
                if x_col == "time":
                    frame["time"] = pd.to_datetime(frame["time"], errors="coerce", utc=True)
                    frame = frame[frame["time"].notna()]
                frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
                frame = frame[frame["value"].notna()].copy()
                if selected_sensors:
                    frame = frame[frame["trace_param_name"].astype(str).isin(selected_sensors)]
                frame = frame.sort_values(["cycle_index", x_col])
                row_count = int(len(frame))
                chart_frame, chart_x_col = _trace_chart_x_frame(frame)
                line_chart = _line_chart_payload(
                    chart_frame,
                    x_column=chart_x_col,
                    y_column="value",
                    selection=selection,
                    series_columns=_trace_series_columns(chart_frame),
                    label_columns=["phase", "lot_id", "slot_no", "wafer_id"],
                )
                columns = [
                    "time",
                    "step_time",
                    "period",
                    "phase",
                    "cycle_index",
                    "pm_date",
                    "trace_param_name",
                    "value",
                    "root_lot_id",
                    "lot_id",
                    "wafer_id",
                    "ch_step",
                    "group",
                    "slot_no",
                ]
                visible_columns = [column for column in columns if column in frame.columns]
                compat_frame = frame.head(_compat_row_limit(selection))
                trend_rows = [_camelize_mapping(row) for row in compat_frame[visible_columns].to_dict(orient="records")]
            else:
                warnings.append("trace data에 날짜/time/value/trace_param_name 컬럼이 없어 상세 plot을 건너뜁니다.")

        # decomp_data에서 shape/jitter 상세 데이터를 읽습니다.
        _SHAPE_COLS = [DATE_COLUMN, "ref_dates", "phase", "value", "group", "lot_id", "slot_no"]
        _JITTER_COLS = [DATE_COLUMN, "ref_dates", "lot_id", "slot_no", "jitter_rms", "level", "group"]
        shape_files = selectors.iter_decomp_files(selection, comp_dt=current_pm_date, param_names=selected_sensors, file_name="shape.parquet")
        jitter_files = selectors.iter_decomp_files(selection, comp_dt=current_pm_date, param_names=selected_sensors, file_name="jitter.parquet")
        shape_frames, _ = _read_frames(shape_files, columns=_SHAPE_COLS, warnings=warnings)
        jitter_frames, _ = _read_frames(jitter_files, columns=_JITTER_COLS, warnings=warnings)
        if shape_frames:
            sf = pd.concat(shape_frames, ignore_index=True)
            if {DATE_COLUMN, "phase", "value"}.issubset(sf.columns):
                sf = sf.rename(columns={"value": "shape", "phase": "norm_phase"})
                sf = _filter_selected_cycles(_raw_cycle_frame(sf, cycle_map), selected_ref_dates)
                sf["shape"] = pd.to_numeric(sf["shape"], errors="coerce")
                sf["norm_phase"] = pd.to_numeric(sf.get("norm_phase", pd.Series(dtype=float)), errors="coerce")
                sf = sf[sf["shape"].notna() & sf["norm_phase"].notna()].copy()
                _vis = [c for c in ["norm_phase", "shape", "ch_step", "lot_id", "slot_no", "group",
                                    "cycle_index", "phase", "pm_date"]
                        if c in sf.columns]
                shape_rows = [_camelize_mapping(r) for r in sf[_vis].to_dict(orient="records")]
        if jitter_frames:
            jf = pd.concat(jitter_frames, ignore_index=True)
            if {DATE_COLUMN, "jitter_rms", "group"}.issubset(jf.columns):
                jf = _filter_selected_cycles(_raw_cycle_frame(jf, cycle_map), selected_ref_dates)
                jf["jitter_rms"] = pd.to_numeric(jf["jitter_rms"], errors="coerce")
                jf = jf[jf["jitter_rms"].notna()].copy()
                _jvis = [c for c in ["lot_id", "slot_no", "jitter_rms", "level", "group", "ch_step",
                                     "cycle_index", "phase", "pm_date"]
                         if c in jf.columns]
                jitter_rows = [_camelize_mapping(r) for r in jf[_jvis].to_dict(orient="records")]

    return {
        "fileCount": raw_file_count,
        "scoreFileCount": score_file_count,
        "rowCount": row_count,
        "worstSensor": rank_rows[0] if rank_rows else None,
        "summaryRows": rank_rows,
        "trendRows": trend_rows,
        "lineChart": line_chart,
        "shapeRows": shape_rows,
        "jitterRows": jitter_rows,
        "scoreTrendRows": _score_trend_rows(score_frame, cycle_map, selected_ref_dates),
        "cycleSummary": _cycle_summary(score_frame, cycle_map, selected_ref_dates),
        "refCycles": _ref_cycle_rows(cycle_map, selected_ref_dates),
    }


def _numeric_wavelength_columns(columns: Iterable[object]) -> list[object]:
    """wide OES schema에서 wavelength로 보이는 컬럼을 찾습니다."""

    wavelength_columns: list[object] = []
    id_names = {name.lower() for name in OES_ID_COLUMNS}
    for column in columns:
        name = str(column)
        if name.lower() in id_names:
            continue
        try:
            wavelength = float(name)
        except ValueError:
            continue
        if 100 <= wavelength <= 1200:
            wavelength_columns.append(column)
    return wavelength_columns


def _normalize_oes(frame: pd.DataFrame, warnings: list[str]) -> pd.DataFrame:
    """OES wide/long schema를 step-wavelength-value long schema로 정규화합니다."""

    if {"wavelength", "value"}.issubset(frame.columns):
        long_frame = frame.copy()
    else:
        wavelength_columns = _numeric_wavelength_columns(frame.columns)
        if not wavelength_columns:
            warnings.append("OES data에서 wavelength 컬럼을 찾지 못했습니다.")
            return frame.iloc[0:0].copy()
        id_columns = [column for column in frame.columns if column not in wavelength_columns]
        long_frame = frame.melt(
            id_vars=id_columns,
            value_vars=wavelength_columns,
            var_name="wavelength",
            value_name="value",
        )

    if "rcp_step" not in long_frame.columns and "step_seq" in long_frame.columns:
        long_frame["rcp_step"] = long_frame["step_seq"]
    if "rcp_step" not in long_frame.columns:
        long_frame["rcp_step"] = "unknown"
    long_frame["wavelength"] = pd.to_numeric(long_frame["wavelength"], errors="coerce")
    long_frame["value"] = pd.to_numeric(long_frame["value"], errors="coerce")
    return long_frame[long_frame["wavelength"].notna() & long_frame["value"].notna()].copy()


def _prepare_oes(selection: dict[str, object], current_pm_date: str, warnings: list[str]) -> dict[str, Any]:
    """result 기반 OES rank와 data 기반 spectrum 상세를 준비합니다."""

    score_frame, score_file_count = _read_score(selection, "oes", warnings)
    cycle_map = _cycle_map(score_frame, current_pm_date)
    selected_ref_dates = _selected_ref_dates(selection, cycle_map)
    rank_rows = _oes_rank_rows(score_frame, current_pm_date)
    selected_step = str(selection.get("selectedStep") or (rank_rows[0].get("step") if rank_rows else "") or "")

    detail_rows: list[dict[str, Any]] = []
    heatmap: dict[str, Any] = {"width": 0, "height": 0, "wavelengths": [], "phases": [], "ref": [], "comp": [], "oob": []}
    line_chart: dict[str, Any] = {"series": [], "xDomain": [None, None], "yDomain": [None, None]}
    spectrum_chart: dict[str, Any] = {"series": [], "xDomain": [None, None], "yDomain": [None, None]}
    raw_file_count = 0
    row_count = 0
    if selection.get("includeDetails", True):
        _oes_source = str(selection.get("oesDataSource") or "oes")
        raw_selection = _selection_with_raw_dt_values(selection, current_pm_date, selected_ref_dates)
        files = selectors.iter_raw_files(raw_selection, data_source=_oes_source, trace_param_names=[])
        frames, raw_file_count = _read_frames(files, columns=None, warnings=warnings)
        if not frames:
            files = selectors.iter_raw_files(raw_selection, data_source="oes_processed", trace_param_names=[])
            frames, raw_file_count = _read_frames(files, columns=None, warnings=warnings)
        if frames:
            frame = _normalize_oes(pd.concat(frames, ignore_index=True), warnings)
            if {DATE_COLUMN, "rcp_step", "wavelength", "value"}.issubset(frame.columns):
                if "phase" in frame.columns:
                    frame = frame.rename(columns={"phase": "traj_phase"})
                frame = _filter_selected_cycles(_raw_cycle_frame(frame, cycle_map), selected_ref_dates)
                frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
                if selected_step:
                    frame = frame[frame["rcp_step"].astype(str) == selected_step]
                frame = frame[frame["value"].notna()].copy()
                if "traj_phase" in frame.columns:
                    frame["traj_phase"] = pd.to_numeric(frame["traj_phase"], errors="coerce")
                    frame = frame[frame["traj_phase"].notna()]
                    frame = frame.sort_values(["cycle_index", "traj_phase"])
                else:
                    frame = frame.sort_values(["cycle_index", "wavelength"])
                step_frame = frame.copy()
                heatmap = _oes_heatmap_payload(step_frame, selection)
                spectrum_chart = _oes_spectrum_payload(step_frame, selection)
                selected_wl = str(selection.get("selectedWavelength") or "")
                if selected_wl:
                    try:
                        wl_val = float(selected_wl)
                        frame = step_frame[step_frame["wavelength"].round(1) == round(wl_val, 1)].copy()
                    except (ValueError, TypeError):
                        frame = step_frame.iloc[0:0].copy()
                else:
                    frame = step_frame
                if "traj_phase" in frame.columns:
                    frame["chart_x"] = pd.to_numeric(frame["traj_phase"], errors="coerce")
                else:
                    frame["chart_x"] = frame.groupby(["phase", "cycle_index"], dropna=False).cumcount()
                row_count = int(len(frame))
                line_chart = _line_chart_payload(
                    frame,
                    x_column="chart_x",
                    y_column="value",
                    selection=selection,
                    series_columns=[
                        column
                        for column in ["phase", "cycle_index", "lot_id", "slot_no", "slot_id", "group"]
                        if column in frame.columns
                    ],
                    label_columns=["phase", "lot_id", "slot_no", "slot_id", "group"],
                )
                columns = [
                    "traj_phase",
                    "phase",
                    "cycle_index",
                    "pm_date",
                    "rcp_step",
                    "wavelength",
                    "value",
                    "lot_id",
                    "slot_no",
                    "slot_id",
                    "group",
                    "wafer_end_time",
                ]
                visible_columns = [column for column in columns if column in frame.columns]
                compat_frame = frame.head(_compat_row_limit(selection))
                detail_rows = [_camelize_mapping(row) for row in compat_frame[visible_columns].to_dict(orient="records")]
            else:
                warnings.append("OES data에 날짜/rcp_step/wavelength/value 컬럼이 없어 상세 plot을 건너뜁니다.")

    step_rows = []
    if rank_rows:
        rank_frame = pd.DataFrame(rank_rows)
        if {"step", "score", "wavelength"}.issubset(rank_frame.columns):
            grouped = (
                rank_frame.groupby("step", dropna=False)
                .agg(wavelengthCount=("wavelength", "count"), minScore=("score", "min"), maxScore=("score", "max"))
                .reset_index()
                .sort_values(["minScore", "step"], ascending=[True, True])
            )
            step_rows = grouped.to_dict(orient="records")

    worst = rank_rows[0] if rank_rows else None
    return {
        "fileCount": raw_file_count,
        "scoreFileCount": score_file_count,
        "rowCount": row_count,
        "worstStep": worst.get("step") if worst else None,
        "worstWavelength": worst,
        "summaryRows": rank_rows,
        "stepRows": step_rows,
        "detailRows": detail_rows,
        "trajectoryRows": detail_rows,
        "heatmap": heatmap,
        "lineChart": line_chart,
        "spectrumChart": spectrum_chart,
        "scoreTrendRows": _score_trend_rows(score_frame, cycle_map, selected_ref_dates),
        "cycleSummary": _cycle_summary(score_frame, cycle_map, selected_ref_dates),
        "refCycles": _ref_cycle_rows(cycle_map, selected_ref_dates),
    }


def _empty_response(selection: dict[str, object], current_pm_date: str, warnings: list[str]) -> dict[str, Any]:
    """조회 결과가 없을 때도 동일한 응답 형태를 반환합니다."""

    return {
        "filters": _build_filter_response(selection),
        "window": {"pmTimestamp": current_pm_date, "pmDate": current_pm_date},
        "trace": {
            "fileCount": 0,
            "scoreFileCount": 0,
            "rowCount": 0,
            "worstSensor": None,
            "summaryRows": [],
            "trendRows": [],
            "lineChart": {"series": [], "xDomain": [None, None], "yDomain": [None, None]},
            "shapeRows": [],
            "jitterRows": [],
            "scoreTrendRows": [],
            "cycleSummary": [],
            "refCycles": [],
        },
        "oes": {
            "fileCount": 0,
            "scoreFileCount": 0,
            "rowCount": 0,
            "worstStep": None,
            "worstWavelength": None,
            "summaryRows": [],
            "stepRows": [],
            "detailRows": [],
            "trajectoryRows": [],
            "heatmap": {"width": 0, "height": 0, "wavelengths": [], "phases": [], "ref": [], "comp": [], "oob": []},
            "lineChart": {"series": [], "xDomain": [None, None], "yDomain": [None, None]},
            "spectrumChart": {"series": [], "xDomain": [None, None], "yDomain": [None, None]},
            "scoreTrendRows": [],
            "cycleSummary": [],
            "refCycles": [],
        },
        "warnings": warnings,
    }


def _build_filter_response(selection: dict[str, object]) -> dict[str, Any]:
    """요청 필터를 응답용으로 정리합니다."""

    keys = [
        "lineId",
        "eqpId",
        "chamberId",
        "fdcBin",
        "type",
        "ppid",
        "recipeId",
        "traceParamNames",
        "traceDataSource",
        "oesDataSource",
        "selectedStep",
        "selectedWavelength",
        "refPmDates",
        "limit",
        "maxPoints",
        "xStart",
        "xEnd",
        "heatmapXBins",
        "heatmapYBins",
    ]
    return {key: _json_safe_value(selection.get(key)) for key in keys}


@lru_cache(maxsize=4096)
def _score_file_dates(path_text: str, mtime_ns: int, size: int) -> tuple[str, ...]:
    """score 파일 하나에서 읽은 PM 날짜 목록을 캐시합니다."""

    frame = selectors.read_parquet(Path(path_text), [DATE_COLUMN])
    if DATE_COLUMN not in frame.columns:
        return tuple()
    return tuple(sorted({_date_key(value) for value in frame[DATE_COLUMN].dropna().unique().tolist()}))


def _collect_pm_dates(warnings: list[str], selection: dict[str, object] | None = None) -> list[str]:
    """result 전체에서 PM 날짜 목록을 수집합니다."""

    if not selection or not selection.get("lineId") or not selection.get("eqpId"):
        return []
    if selection.get("pmTimestamp"):
        try:
            return [_date_key(selection["pmTimestamp"])]
        except (TypeError, ValueError):
            return [str(selection["pmTimestamp"])]

    dates: set[str] = set()
    try:
        files = [
            *selectors.iter_score_files(selection or {}, data_type="trace"),
            *selectors.iter_score_files(selection or {}, data_type="oes"),
        ]
    except (FileNotFoundError, NotADirectoryError):
        return []
    for path in files:
        try:
            stat = path.stat()
            dates.update(_score_file_dates(str(path), stat.st_mtime_ns, stat.st_size))
        except Exception as exc:
            warnings.append(f"score 날짜 읽기 실패: {path.name} ({exc})")
            continue
    return sorted(dates)


def _has_time_part(value: str) -> bool:
    """raw dt 값에 시각 정보가 포함되어 있는지 확인합니다."""

    text = str(value)
    return (len(text) > 10 and text[10:11] in {" ", "T"}) or ":" in text


def _meta_pm_dates(
    selection: dict[str, object] | None,
    options: dict[str, list[str]],
    warnings: list[str],
) -> list[str]:
    """PM 시점 dropdown에 노출할 날짜 후보를 결정합니다."""

    raw_dt_values = options.get("dt", [])
    if selection and selection.get("fdcBin") and any(_has_time_part(value) for value in raw_dt_values):
        return raw_dt_values
    pm_dates = _collect_pm_dates(warnings, selection)
    return pm_dates or raw_dt_values


def get_meta(selection: dict[str, object] | None = None) -> dict[str, object]:
    """PM SPIDER 데이터 선택 메타데이터를 반환합니다."""

    warnings: list[str] = []
    try:
        options = selectors.collect_partition_options(selection)
    except FileNotFoundError as exc:
        raise PmComparisonServiceError(str(exc), status_code=404) from exc
    except NotADirectoryError as exc:
        raise PmComparisonServiceError(str(exc), status_code=400) from exc

    pm_dates = _meta_pm_dates(selection, options, warnings)

    return {
        "lineIds": options.get("line_id", []),
        "eqpIds": options.get("eqp_id", []),
        "fdcBins": options.get("fdc_bin", []),
        "dtValues": options.get("dt", []),
        "pmDates": pm_dates or options.get("dt", []),
        "types": options.get("type", []),
        "ppids": options.get("ppid", []),
        "recipeIds": options.get("recipe_id", []),
        "dataSources": options.get("data_source", []),
        "traceParamNames": options.get("trace_param_name", []),
        "warnings": warnings,
    }


def compare_pm_window(selection: dict[str, object]) -> dict[str, Any]:
    """PM 주기 기준 score rank와 raw 상세 데이터를 반환합니다."""

    warnings: list[str] = []
    current_pm_date = _selected_pm_date(selection)
    try:
        trace = _prepare_trace(selection, current_pm_date, warnings)
        oes = _prepare_oes(selection, current_pm_date, warnings)
    except FileNotFoundError as exc:
        raise PmComparisonServiceError(str(exc), status_code=404) from exc
    except NotADirectoryError as exc:
        raise PmComparisonServiceError(str(exc), status_code=400) from exc

    if not trace["summaryRows"] and not oes["summaryRows"]:
        return _empty_response(selection, current_pm_date, warnings)

    return {
        "filters": _build_filter_response(selection),
        "window": {"pmTimestamp": current_pm_date, "pmDate": current_pm_date},
        "trace": trace,
        "oes": oes,
        "warnings": warnings,
    }
