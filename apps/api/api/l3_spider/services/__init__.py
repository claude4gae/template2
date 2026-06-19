# =============================================================================
# 모듈: L3 Spider 서비스
# 주요 함수: get_meta, get_summary, get_data
# 주요 가정: Parquet 원본 컬럼은 snake_case이고 API 응답은 camelCase입니다.
# =============================================================================
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from django.conf import settings

import numpy as np
import pandas as pd

from api.l3_spider import selectors

SUMMARY_COLUMNS = ["step_seq", "ppid", "eqp_id", "eqc", "bin_name", "display_status"]
# 파일명에서 step_seq/ppid 파싱 성공 시 파일에서 읽을 컬럼 (절반으로 감소)
_SUMMARY_COLUMNS_SLIM = ["eqc", "bin_name", "display_status"]
_SUMMARY_DEDUP_KEYS = ["step_seq", "ppid", "eqc", "bin_name", "display_status"]
CHART_COLUMNS = [
    "tkin_time",
    "tkout_time",
    "owning",
    "step_seq",
    "ppid",
    "root_lot_id",
    "lot_id",
    "wafer_id",
    "eqp_id",
    "chamber_id",
    "eqc",
    "bin_name",
    "bin_value",
    "prop_over_50",
    "q1",
    "q3",
    "iqr",
    "lsl",
    "usl",
    "seq_idx",
    "risk_score",
    "display_status",
    "comment",
]
ANOMALY_STATUSES = {"Warning", "High Risk Chamber"}


class L3SpiderServiceError(Exception):
    """L3 Spider 서비스 오류를 HTTP 상태와 함께 표현합니다."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        """오류 메시지와 상태 코드를 저장합니다."""

        super().__init__(message)
        self.status_code = status_code


def _snake_to_camel(value: str) -> str:
    """snake_case 문자열을 camelCase로 변환합니다."""

    parts = value.split("_")
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def _camelize_mapping(row: dict[str, Any]) -> dict[str, Any]:
    """dict 키를 camelCase로 변환합니다."""

    return {_snake_to_camel(key): _json_safe_value(value) for key, value in row.items()}


def _json_safe_value(value: Any) -> Any:
    """JSON 직렬화 가능한 값으로 정리합니다."""

    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return _json_safe_value(value.item())
    return value


def _normalize_display_status(frame: pd.DataFrame) -> pd.DataFrame:
    """표시 상태 컬럼명을 정리하고 상태 라벨을 정규화합니다."""

    if "display status" in frame.columns and "display_status" not in frame.columns:
        frame = frame.rename(columns={"display status": "display_status"})
    if "display_status" in frame.columns:
        frame["display_status"] = frame["display_status"].replace({"Single Spike": "Warning"})
    return frame


def _empty_stats() -> dict[str, int]:
    """빈 통계 응답을 반환합니다."""

    return {
        "total": 0,
        "normal": 0,
        "warning": 0,
        "risk": 0,
        "anomalySteps": 0,
        "highRiskEqpchs": 0,
    }


def _has_required_selection(selection: dict[str, object]) -> bool:
    """필수 선택 조건이 모두 있는지 확인합니다."""

    return all(selection.get(key) for key in ("dates", "lineIds", "processIds", "edsSteps"))


def _parse_filename_key(path: Path) -> tuple[str, str] | None:
    """파일명에서 (step_seq, ppid)를 파싱합니다.

    persistence.py 의 basename_template=f"{name_prefix}#{{i}}" 로 저장된
    파일명 패턴을 지원합니다.
    예: STEP_001#PPID_A#0 또는 STEP_001#PPID_A#0.parquet → ('STEP_001', 'PPID_A')
    파싱 불가(data.parquet, 구형 포맷 등)이면 None을 반환합니다.
    """
    try:
        name = path.name
        if name.endswith(".parquet"):
            name = name[: -len(".parquet")]
        parts = name.split("#")
        if len(parts) == 3 and parts[0] and parts[1]:
            return parts[0], parts[1]
    except Exception:
        pass
    return None


def _add_path_context(frame: pd.DataFrame, path: Path, *, override_filename_keys: bool = False) -> pd.DataFrame:
    """파일 경로에서 유도 가능한 컨텍스트 컬럼을 보강합니다."""

    relative_parts = path.relative_to(selectors.get_data_root()).parts
    if len(relative_parts) >= 4:
        frame["eds_step"] = relative_parts[3]

    parsed = _parse_filename_key(path)
    if not parsed:
        return frame

    step_seq, ppid = parsed
    if override_filename_keys or "step_seq" not in frame.columns:
        frame["step_seq"] = step_seq
    else:
        frame["step_seq"] = frame["step_seq"].fillna(step_seq)
    if override_filename_keys or "ppid" not in frame.columns:
        frame["ppid"] = ppid
    else:
        frame["ppid"] = frame["ppid"].fillna(ppid)
    return frame


def _read_frames(selection: dict[str, object], columns: list[str]) -> list[pd.DataFrame]:
    """선택된 파일들을 DataFrame 목록으로 읽습니다."""

    frames: list[pd.DataFrame] = []
    try:
        files = list(selectors.iter_data_files(selection))
    except FileNotFoundError as exc:
        raise L3SpiderServiceError(str(exc), status_code=404) from exc
    except NotADirectoryError as exc:
        raise L3SpiderServiceError(str(exc), status_code=400) from exc

    for path in files:
        try:
            frame = selectors.read_parquet_columns(path, columns)
            frame = _normalize_display_status(frame)
            frame = _add_path_context(frame, path)
            frames.append(frame)
        except Exception as exc:
            print(f"[WARN] L3 Spider parquet read failed: {path}: {exc}")
    return frames


def _read_summary_frames(selection: dict[str, object]) -> list[pd.DataFrame]:
    """summary 전용 최적화 읽기.

    파일명이 STEP#PPID#N 또는 STEP#PPID#N.parquet 형식이면 step_seq·ppid를 파일명에서 가져오고
    eqc·bin_name·display_status 3컬럼만 읽는다(6컬럼 → 3컬럼).
    구형 포맷(data.parquet 등)은 SUMMARY_COLUMNS 전체를 읽는 fallback 사용.
    두 경우 모두 파일당 즉시 drop_duplicates로 메모리를 줄인다.
    """
    frames: list[pd.DataFrame] = []
    try:
        files = list(selectors.iter_data_files(selection))
    except FileNotFoundError as exc:
        raise L3SpiderServiceError(str(exc), status_code=404) from exc
    except NotADirectoryError as exc:
        raise L3SpiderServiceError(str(exc), status_code=400) from exc

    for path in files:
        try:
            parsed = _parse_filename_key(path)
            cols = _SUMMARY_COLUMNS_SLIM if parsed else SUMMARY_COLUMNS
            frame = selectors.read_parquet_columns(path, cols)
            frame = _normalize_display_status(frame)
            frame = _add_path_context(frame, path, override_filename_keys=bool(parsed))
            available_dedup = [c for c in _SUMMARY_DEDUP_KEYS if c in frame.columns]
            frame = frame.drop_duplicates(subset=available_dedup)
            frames.append(frame)
        except Exception as exc:
            print(f"[WARN] L3 Spider summary read failed: {path}: {exc}")
    return frames


def _sample_chart_points(frame: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    """차트 패널별 최대 표시 점 수를 제한합니다."""

    max_points = getattr(settings, "L3_SPIDER_MAX_CHART_POINTS_PER_PANEL", 2000)
    if max_points <= 0 or frame.empty:
        return frame

    sampled: list[pd.DataFrame] = []
    available_group_columns = [column for column in group_columns if column in frame.columns]
    if not available_group_columns:
        return frame.head(max_points)

    for _, group in frame.groupby(available_group_columns, sort=False, dropna=False):
        if len(group) <= max_points:
            sampled.append(group)
            continue

        if "display_status" in group.columns:
            anomaly = group[group["display_status"].isin(ANOMALY_STATUSES)]
        else:
            anomaly = group.iloc[0:0]
        remaining_slots = max_points - len(anomaly)
        if remaining_slots <= 0:
            sampled.append(anomaly)
            continue

        others = group[~group.index.isin(anomaly.index)]
        sampled.append(
            pd.concat(
                [
                    anomaly,
                    others.sample(n=min(remaining_slots, len(others)), random_state=42),
                ]
            )
        )

    return pd.concat(sampled, ignore_index=True) if sampled else frame.iloc[0:0]


def get_meta() -> dict[str, object]:
    """사용 가능한 날짜/라인/프로세스/EDS step 메타데이터를 반환합니다."""

    dates: set[str] = set()
    line_ids: set[str] = set()
    process_ids: set[str] = set()
    eds_steps: set[str] = set()
    availability: dict[str, dict[str, dict[str, set[str]]]] = {}

    try:
        files = list(selectors.iter_all_data_files())
    except FileNotFoundError as exc:
        raise L3SpiderServiceError(str(exc), status_code=404) from exc
    except NotADirectoryError as exc:
        raise L3SpiderServiceError(str(exc), status_code=400) from exc

    root = selectors.get_data_root()
    for path in files:
        parts = path.relative_to(root).parts
        if len(parts) != 5:
            continue
        date, line_id, process_id, eds_step = parts[:4]
        dates.add(date)
        line_ids.add(line_id)
        process_ids.add(process_id)
        eds_steps.add(eds_step)
        availability.setdefault(date, {}).setdefault(line_id, {}).setdefault(process_id, set()).add(eds_step)

    return {
        "dates": sorted(dates),
        "lineIds": sorted(line_ids),
        "processIds": sorted(process_ids),
        "edsSteps": sorted(eds_steps),
        "availability": {
            date: {
                line_id: {
                    process_id: sorted(process_eds_steps)
                    for process_id, process_eds_steps in sorted(processes.items())
                }
                for line_id, processes in sorted(lines.items())
            }
            for date, lines in sorted(availability.items())
        },
    }


def get_summary(selection: dict[str, object]) -> dict[str, object]:
    """선택 조건의 이상감지 요약 정보를 반환합니다."""

    empty = {"stats": _empty_stats(), "edsStepSeqs": {}, "edsStepPpids": {}, "stepPpids": {}, "ppidEqcs": {}, "ppidHighRiskEqcs": {}, "ppidBins": {}, "eqcBins": {}, "eqcAnomalyBins": {}, "eqcHighRiskBins": {}, "bins": [], "anomalies": []}
    if not _has_required_selection(selection):
        return empty

    frames = _read_summary_frames(selection)
    if not frames:
        return empty

    merged = pd.concat(frames, ignore_index=True)
    merged = _normalize_display_status(merged)
    if "display_status" not in merged.columns:
        return empty

    status = merged["display_status"]
    anomaly_mask = status.isin(ANOMALY_STATUSES)
    high_risk_mask = status == "High Risk Chamber"
    stats = {
        "total": int(len(merged)),
        "normal": int((status == "Normal (Ref)").sum()),
        "warning": int((status == "Warning").sum()),
        "risk": int(high_risk_mask.sum()),
        "anomalySteps": int(merged.loc[anomaly_mask, "step_seq"].dropna().nunique())
        if "step_seq" in merged.columns
        else 0,
        "highRiskEqpchs": int(merged.loc[high_risk_mask, "eqc"].dropna().nunique())
        if "eqc" in merged.columns
        else 0,
    }

    eds_step_seqs: dict[str, list[str]] = {}
    if {"eds_step", "step_seq"}.issubset(merged.columns):
        pairs = merged[["eds_step", "step_seq"]].drop_duplicates().sort_values(["eds_step", "step_seq"])
        eds_step_seqs = {
            str(eds): sorted(group["step_seq"].dropna().astype(str).tolist())
            for eds, group in pairs.groupby("eds_step", sort=True)
        }

    eds_step_ppids: dict[str, list[str]] = {}
    if {"eds_step", "step_seq", "ppid"}.issubset(merged.columns):
        pairs = merged[["eds_step", "step_seq", "ppid"]].drop_duplicates().sort_values(
            ["eds_step", "step_seq", "ppid"]
        )
        eds_step_ppids = {
            f"{str(eds)}|||{str(step)}": sorted(group["ppid"].dropna().astype(str).tolist())
            for (eds, step), group in pairs.groupby(["eds_step", "step_seq"], sort=True)
        }

    step_ppids: dict[str, list[str]] = {}
    if {"step_seq", "ppid"}.issubset(merged.columns):
        pairs = merged[["step_seq", "ppid"]].drop_duplicates().sort_values(["step_seq", "ppid"])
        step_ppids = {
            str(step): group["ppid"].dropna().astype(str).tolist()
            for step, group in pairs.groupby("step_seq", sort=True)
        }

    anomalies: list[dict[str, Any]] = []
    anomaly_columns = ["eds_step", "step_seq", "ppid", "eqc", "bin_name"]
    if all(column in merged.columns for column in anomaly_columns):
        anomalies = [
            _camelize_mapping(row)
            for row in (
                merged.loc[high_risk_mask, anomaly_columns]
                .drop_duplicates()
                .sort_values(anomaly_columns)
                .astype(str)
                .to_dict(orient="records")
            )
        ]

    ppid_eqcs: dict[str, list[str]] = {}
    if {"ppid", "eqc"}.issubset(merged.columns):
        pairs = merged[["ppid", "eqc"]].drop_duplicates().sort_values(["ppid", "eqc"])
        ppid_eqcs = {
            str(ppid): sorted(group["eqc"].dropna().astype(str).tolist())
            for ppid, group in pairs.groupby("ppid", sort=True)
        }

    ppid_high_risk_eqcs: dict[str, list[str]] = {}
    if {"ppid", "eqc", "display_status"}.issubset(merged.columns):
        high_risk_pairs = (
            merged.loc[high_risk_mask, ["ppid", "eqc"]]
            .drop_duplicates()
            .sort_values(["ppid", "eqc"])
        )
        ppid_high_risk_eqcs = {
            str(ppid): sorted(group["eqc"].dropna().astype(str).tolist())
            for ppid, group in high_risk_pairs.groupby("ppid", sort=True)
        }

    ppid_bins: dict[str, list[str]] = {}
    if {"ppid", "bin_name"}.issubset(merged.columns):
        pairs = merged[["ppid", "bin_name"]].drop_duplicates().sort_values(["ppid", "bin_name"])
        ppid_bins = {
            str(ppid): sorted(group["bin_name"].dropna().astype(str).tolist())
            for ppid, group in pairs.groupby("ppid", sort=True)
        }

    eqc_bins: dict[str, list[str]] = {}
    if {"eqc", "bin_name"}.issubset(merged.columns):
        pairs = merged[["eqc", "bin_name"]].drop_duplicates().sort_values(["eqc", "bin_name"])
        eqc_bins = {
            str(eqc): sorted(group["bin_name"].dropna().astype(str).tolist())
            for eqc, group in pairs.groupby("eqc", sort=True)
        }

    eqc_anomaly_bins: dict[str, list[str]] = {}
    if {"eqc", "bin_name", "display_status"}.issubset(merged.columns):
        anomaly_pairs = (
            merged.loc[merged["display_status"].isin(ANOMALY_STATUSES), ["eqc", "bin_name"]]
            .drop_duplicates()
            .sort_values(["eqc", "bin_name"])
        )
        eqc_anomaly_bins = {
            str(eqc): sorted(group["bin_name"].dropna().astype(str).tolist())
            for eqc, group in anomaly_pairs.groupby("eqc", sort=True)
        }

    eqc_high_risk_bins: dict[str, list[str]] = {}
    if {"eqc", "bin_name", "display_status"}.issubset(merged.columns):
        high_risk_bin_pairs = (
            merged.loc[high_risk_mask, ["eqc", "bin_name"]]
            .drop_duplicates()
            .sort_values(["eqc", "bin_name"])
        )
        eqc_high_risk_bins = {
            str(eqc): sorted(group["bin_name"].dropna().astype(str).tolist())
            for eqc, group in high_risk_bin_pairs.groupby("eqc", sort=True)
        }

    bins = (
        sorted(merged["bin_name"].dropna().astype(str).unique().tolist())
        if "bin_name" in merged.columns
        else []
    )
    return {
        "stats": stats,
        "edsStepSeqs": eds_step_seqs,
        "edsStepPpids": eds_step_ppids,
        "stepPpids": step_ppids,
        "ppidEqcs": ppid_eqcs,
        "ppidHighRiskEqcs": ppid_high_risk_eqcs,
        "ppidBins": ppid_bins,
        "eqcBins": eqc_bins,
        "eqcAnomalyBins": eqc_anomaly_bins,
        "eqcHighRiskBins": eqc_high_risk_bins,
        "bins": bins,
        "anomalies": anomalies,
    }


def get_data(selection: dict[str, object]) -> dict[str, object]:
    """선택 조건과 필터에 맞는 차트 행 데이터를 반환합니다."""

    if not _has_required_selection(selection):
        return {"rows": []}

    selected_eqcs = set(selection.get("selectedEqcs") or [])
    selected_step_bins = set(selection.get("selectedStepBins") or [])
    selected_ppid_bins = set(selection.get("selectedPpidBins") or [])
    selected_steps = set(selection.get("selectedSteps") or [])
    checked_eds_steps = set(selection.get("checkedEdsSteps") or [])
    checked_ppids = set(selection.get("checkedPpids") or [])
    checked_bins = set(selection.get("checkedBins") or [])

    if not selected_eqcs and not selected_step_bins and not selected_ppid_bins and not selected_steps:
        return {"rows": []}

    frames = []
    for frame in _read_frames(selection, CHART_COLUMNS):
        if checked_eds_steps and "eds_step" in frame.columns:
            frame = frame[frame["eds_step"].isin(checked_eds_steps)]
        if checked_ppids and "ppid" in frame.columns:
            frame = frame[frame["ppid"].isin(checked_ppids)]
        if checked_bins and "bin_name" in frame.columns:
            frame = frame[frame["bin_name"].isin(checked_bins)]
        if selected_eqcs and "eqc" in frame.columns:
            frame = frame[frame["eqc"].isin(selected_eqcs)]
        if selected_steps and "step_seq" in frame.columns:
            frame = frame[frame["step_seq"].isin(selected_steps)]
        if selected_step_bins and {"step_seq", "bin_name"}.issubset(frame.columns):
            step_bin = frame["step_seq"].astype(str) + "|||" + frame["bin_name"].astype(str)
            frame = frame[step_bin.isin(selected_step_bins)]
        if selected_ppid_bins and {"step_seq", "ppid", "bin_name"}.issubset(frame.columns):
            ppid_bin = (
                frame["step_seq"].astype(str)
                + "|||"
                + frame["ppid"].astype(str)
                + "|||"
                + frame["bin_name"].astype(str)
            )
            frame = frame[ppid_bin.isin(selected_ppid_bins)]
        if not frame.empty:
            frames.append(frame)

    if not frames:
        return {"rows": []}

    merged = pd.concat(frames, ignore_index=True)
    if selected_eqcs:
        merged = _sample_chart_points(merged, ["step_seq", "bin_name"])
    elif checked_bins or selected_step_bins or selected_ppid_bins:
        merged = _sample_chart_points(merged, ["eqc"])

    merged = _normalize_display_status(merged)
    if "comment" not in merged.columns:
        merged["comment"] = None

    for column in ["tkin_time", "tkout_time"]:
        if column in merged.columns:
            try:
                merged[column] = merged[column].dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                merged[column] = merged[column].astype(str)

    float32_columns = merged.select_dtypes(include=["float32"]).columns
    merged[float32_columns] = merged[float32_columns].astype("float64")
    for column in merged.select_dtypes(include=["string", "object"]).columns:
        merged[column] = merged[column].where(merged[column].notna(), other=None)
        merged[column] = merged[column].astype(object)
    merged = merged.replace([np.inf, -np.inf], np.nan)

    return {"rows": [_camelize_mapping(row) for row in merged.to_dict(orient="records")]}


def get_filter_candidates(selection: dict[str, object]) -> dict[str, object]:
    """PPID 선택 경로(date/line/process/eds_step/step_seq#ppid#*)에서 High Risk EQPCH·Bin 후보를 반환합니다."""

    dates = selection.get("dates") or []
    line_ids = selection.get("lineIds") or []
    process_ids = selection.get("processIds") or []
    eds_step = selection.get("edsStep", "")
    step_seq = selection.get("stepSeq", "")
    ppid = selection.get("ppid", "")

    if not all([dates, line_ids, process_ids, eds_step, step_seq, ppid]):
        return {"eqcHighRiskBins": {}}

    frames: list[pd.DataFrame] = []
    try:
        files = list(selectors.iter_filter_candidate_files(dates, line_ids, process_ids, eds_step, step_seq, ppid))
    except (FileNotFoundError, NotADirectoryError) as exc:
        raise L3SpiderServiceError(str(exc), status_code=404) from exc

    for path in files:
        try:
            frame = selectors.read_parquet_columns(path, ["eqc", "bin_name", "display_status"])
            frame = _normalize_display_status(frame)
            frames.append(frame)
        except Exception as exc:
            print(f"[WARN] L3 Spider filter-candidates read failed: {path}: {exc}")

    if not frames:
        return {"eqcHighRiskBins": {}}

    merged = pd.concat(frames, ignore_index=True)

    eqc_high_risk_bins: dict[str, list[str]] = {}
    if {"eqc", "bin_name", "display_status"}.issubset(merged.columns):
        high_risk_mask = merged["display_status"] == "High Risk Chamber"
        pairs = (
            merged.loc[high_risk_mask, ["eqc", "bin_name"]]
            .drop_duplicates()
            .sort_values(["eqc", "bin_name"])
        )
        eqc_high_risk_bins = {
            str(eqc): sorted(group["bin_name"].dropna().astype(str).tolist())
            for eqc, group in pairs.groupby("eqc", sort=True)
        }

    return {"eqcHighRiskBins": eqc_high_risk_bins}
