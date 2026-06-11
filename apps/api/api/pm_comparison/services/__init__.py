# =============================================================================
# 모듈: PM SPIDER 서비스
# 주요 함수: get_meta, compare_pm_window
# 주요 가정: data는 원본, result는 PM 주기별 scoring 결과입니다.
# =============================================================================
from __future__ import annotations

import math
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
    # trace-specific delta columns
    "delta_shape",
    "delta_jitter",
    "delta_level",
    "flag",
    "alarm_pct",
    # oes-specific delta columns
    "delta_spectrum",
    "direction",
    "flagged_wl",
]


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
        return frame
    for column in SCORE_COLUMNS:
        if column not in frame.columns:
            frame[column] = None
    frame = frame.copy()
    frame["line_id"] = frame["line_id"].fillna(selection.get("lineId"))
    frame["eqp_id"] = frame["eqp_id"].fillna(selection.get("eqpId"))
    chamber_id = str(selection.get("chamberId") or "")
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
        return pd.DataFrame(columns=SCORE_COLUMNS), file_count
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

    files = selectors.iter_raw_files(
        selection,
        data_source=str(selection.get("traceDataSource") or "trace"),
        trace_param_names=selected_sensors,
    )
    frames, raw_file_count = _read_frames(files, columns=TRACE_COLUMNS, warnings=warnings)
    trend_rows: list[dict[str, Any]] = []
    row_count = 0
    if frames:
        frame = pd.concat(frames, ignore_index=True)
        if "trace_param_name" not in frame.columns and "name" in frame.columns:
            frame["trace_param_name"] = frame["name"]
        if {"time", "value", DATE_COLUMN, "trace_param_name"}.issubset(frame.columns):
            frame = _filter_selected_cycles(_raw_cycle_frame(frame, cycle_map), selected_ref_dates)
            frame["time"] = pd.to_datetime(frame["time"], errors="coerce", utc=True)
            frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
            frame = frame[frame["time"].notna() & frame["value"].notna()].copy()
            if selected_sensors:
                frame = frame[frame["trace_param_name"].astype(str).isin(selected_sensors)]
            frame = frame.sort_values(["cycle_index", "time"])
            row_count = int(len(frame))
            columns = [
                "time",
                "period",
                "phase",
                "cycle_index",
                "pm_date",
                "trace_param_name",
                "value",
                "root_lot_id",
                "lot_id",
                "wafer_id",
                "step_time",
            ]
            visible_columns = [column for column in columns if column in frame.columns]
            trend_rows = [_camelize_mapping(row) for row in frame[visible_columns].to_dict(orient="records")]
        else:
            warnings.append("trace data에 날짜/time/value/trace_param_name 컬럼이 없어 상세 plot을 건너뜁니다.")

    return {
        "fileCount": raw_file_count,
        "scoreFileCount": score_file_count,
        "rowCount": row_count,
        "worstSensor": rank_rows[0] if rank_rows else None,
        "summaryRows": rank_rows,
        "trendRows": trend_rows,
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

    files = selectors.iter_raw_files(
        selection,
        data_source=str(selection.get("oesDataSource") or "oes"),
        trace_param_names=[],
    )
    frames, raw_file_count = _read_frames(files, columns=None, warnings=warnings)
    detail_rows: list[dict[str, Any]] = []
    row_count = 0
    if frames:
        frame = _normalize_oes(pd.concat(frames, ignore_index=True), warnings)
        if {DATE_COLUMN, "rcp_step", "wavelength", "value"}.issubset(frame.columns):
            frame = _filter_selected_cycles(_raw_cycle_frame(frame, cycle_map), selected_ref_dates)
            frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
            if selected_step:
                frame = frame[frame["rcp_step"].astype(str) == selected_step]
            frame = frame[frame["value"].notna()].copy().sort_values(["cycle_index", "wavelength"])
            row_count = int(len(frame))
            columns = [
                "phase",
                "cycle_index",
                "pm_date",
                "rcp_step",
                "wavelength",
                "value",
                "lot_id",
                "slot_id",
                "wafer_end_time",
            ]
            visible_columns = [column for column in columns if column in frame.columns]
            detail_rows = [_camelize_mapping(row) for row in frame[visible_columns].to_dict(orient="records")]
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
    ]
    return {key: _json_safe_value(selection.get(key)) for key in keys}


def _collect_pm_dates(warnings: list[str]) -> list[str]:
    """result 전체에서 PM 날짜 목록을 수집합니다."""

    dates: set[str] = set()
    try:
        score_root = selectors.ensure_dataset_root(selectors.SCORE_DIR_NAME)
    except (FileNotFoundError, NotADirectoryError):
        return []
    for path in score_root.rglob("*.parquet"):
        try:
            frame = selectors.read_parquet(path, [DATE_COLUMN])
        except Exception as exc:
            warnings.append(f"score 날짜 읽기 실패: {path.name} ({exc})")
            continue
        if DATE_COLUMN in frame.columns:
            dates.update(_date_key(value) for value in frame[DATE_COLUMN].dropna().unique().tolist())
    return sorted(dates)


def get_meta() -> dict[str, object]:
    """PM SPIDER 데이터 선택 메타데이터를 반환합니다."""

    warnings: list[str] = []
    try:
        options = selectors.collect_partition_options()
    except FileNotFoundError as exc:
        raise PmComparisonServiceError(str(exc), status_code=404) from exc
    except NotADirectoryError as exc:
        raise PmComparisonServiceError(str(exc), status_code=400) from exc

    return {
        "lineIds": options.get("line_id", []),
        "eqpIds": options.get("eqp_id", []),
        "fdcBins": options.get("fdc_bin", []),
        "dtValues": options.get("dt", []),
        "pmDates": _collect_pm_dates(warnings),
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
