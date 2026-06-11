# =============================================================================
# 모듈: PM SPIDER 데이터 writer / loader
# 용도: 외부 분석 모듈에서 생성한 DataFrame을 대시보드가 읽는 Parquet 파티션으로
#       저장하거나, 저장된 파일을 그대로 다시 불러올 때 사용합니다.
#
# 경로 규칙 (selectors.py 와 동일한 파티션 계약)
#   result/
#     line_id=<>/eqp_id=<>/chamber_id=<>/type=<ag|process>/data_type=<trace|oes>/
#   data/
#     line_id=<>/eqp_id=<>/fdc_bin=<>/dt=<YYYY-MM-DD>/type=<ag|process>/
#     ppid=<>/recipe_id=<>/data_source=<trace|oes>/trace_param_name=<>/
# =============================================================================
from __future__ import annotations

import re
from pathlib import Path
from typing import Sequence

import pandas as pd

from . import selectors

# 파티션 값으로 허용되는 문자 (serializers._is_safe_segment 와 동일)
_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9_.-]+$")

# result에서 대시보드가 반드시 읽는 컬럼
_SCORE_REQUIRED = {"날짜", "item_name", "score"}

# data/trace에서 대시보드가 반드시 읽는 컬럼
_TRACE_REQUIRED = {"날짜", "time", "step_time", "value", "trace_param_name"}

# data/OES(long)에서 대시보드가 반드시 읽는 컬럼
_OES_REQUIRED = {"날짜", "rcp_step", "wavelength", "value"}

# OES wide 스키마에서 ID 컬럼으로 간주하는 이름 집합 (소문자)
_OES_ID_NAMES = {
    "line_id", "device_id", "ppid", "recipe_id", "step_seq", "eqp_id",
    "bin_id", "lot_id", "slot_id", "날짜", "wafer_end_time", "rcp_step",
    "name", "time", "wavelength", "value", "fdc_bin", "type",
}

# OES wide 스키마에서 유효한 wavelength 범위 (nm)
_WL_MIN, _WL_MAX = 100.0, 1200.0


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------

def _validate_segment(value: str, field: str) -> str:
    """파티션 값이 경로 안전 문자인지 확인합니다."""
    value = str(value).strip()
    if not value:
        raise ValueError(f"{field} 값이 비어 있습니다.")
    if not _SAFE_SEGMENT.match(value) or ".." in value:
        raise ValueError(
            f"{field}={value!r} 에 허용되지 않는 문자가 포함되어 있습니다. "
            "영문·숫자·_·.·- 만 사용하세요."
        )
    return value


def _check_required(df: pd.DataFrame, required: set[str], label: str) -> None:
    """필수 컬럼이 DataFrame 에 있는지 확인합니다."""
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"{label} DataFrame 에 필수 컬럼이 없습니다: {sorted(missing)}\n"
            f"현재 컬럼: {sorted(df.columns.tolist())}"
        )


def _is_wide_oes(df: pd.DataFrame) -> bool:
    """OES DataFrame 이 wide 형식인지 판별합니다."""
    for col in df.columns:
        name = str(col).lower()
        if name in _OES_ID_NAMES:
            continue
        try:
            wl = float(col)
            if _WL_MIN <= wl <= _WL_MAX:
                return True
        except ValueError:
            pass
    return False


def _make_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_parquet(df: pd.DataFrame, dest: Path) -> Path:
    df.to_parquet(dest, engine="pyarrow", index=False)
    return dest


# ---------------------------------------------------------------------------
# result
# ---------------------------------------------------------------------------

def save_score(
    df: pd.DataFrame,
    *,
    line_id: str,
    eqp_id: str,
    chamber_id: str,
    type: str,
    data_type: str,
    filename: str = "scores.parquet",
    data_root: str | Path | None = None,
) -> Path:
    """score DataFrame 을 대시보드 파티션 경로에 저장합니다.

    Parameters
    ----------
    df:
        저장할 DataFrame. 최소 컬럼: ``날짜``, ``item_name``, ``score``.
        trace 추가 컬럼: ``step``, ``delta_shape``, ``delta_jitter``, ``delta_level``,
        ``flag``, ``alarm_pct``.
        OES 추가 컬럼: ``step``, ``wavelength``, ``delta_spectrum``, ``direction``,
        ``flagged_wl``.
    line_id, eqp_id, chamber_id, type, data_type:
        파티션 키 값. type 은 ``ag`` 또는 ``process``,
        data_type 은 ``trace`` 또는 ``oes``.
    filename:
        파티션 디렉터리 안에 저장될 파일명.
    data_root:
        ``PM_COMPARISON_DATA_ROOT`` 를 직접 지정할 때만 사용합니다.
        생략하면 Django settings 에서 읽습니다.

    Returns
    -------
    저장된 Parquet 파일의 절대 경로.

    Examples
    --------
    >>> save_score(
    ...     score_df,
    ...     line_id="L1", eqp_id="EQP01", chamber_id="CH1",
    ...     type="ag", data_type="trace",
    ... )
    PosixPath('.../result/line_id=L1/eqp_id=EQP01/chamber_id=CH1/type=ag/data_type=trace/scores.parquet')
    """
    _check_required(df, _SCORE_REQUIRED, "result")
    line_id = _validate_segment(line_id, "line_id")
    eqp_id = _validate_segment(eqp_id, "eqp_id")
    chamber_id = _validate_segment(chamber_id, "chamber_id")
    type = _validate_segment(type, "type")
    data_type = _validate_segment(data_type, "data_type")

    root = Path(data_root).expanduser().resolve() if data_root else selectors.get_data_root()
    dest_dir = (
        root / selectors.SCORE_DIR_NAME
        / f"line_id={line_id}"
        / f"eqp_id={eqp_id}"
        / f"chamber_id={chamber_id}"
        / f"type={type}"
        / f"data_type={data_type}"
    )
    _make_dir(dest_dir)
    return _write_parquet(df, dest_dir / filename)


def load_score(
    *,
    line_id: str,
    eqp_id: str,
    chamber_id: str,
    type: str,
    data_type: str,
    data_root: str | Path | None = None,
) -> pd.DataFrame:
    """save_score 로 저장한 파일을 다시 읽어 DataFrame 으로 반환합니다.

    저장된 파일이 없으면 빈 DataFrame 을 반환합니다.
    """
    selection: dict[str, object] = {
        "lineId": line_id,
        "eqpId": eqp_id,
        "chamberId": chamber_id,
        "type": type,
    }
    if data_root:
        root = Path(data_root).expanduser().resolve()
        score_dir = (
            root / selectors.SCORE_DIR_NAME
            / f"line_id={line_id}"
            / f"eqp_id={eqp_id}"
            / f"chamber_id={chamber_id}"
            / f"type={type}"
            / f"data_type={data_type}"
        )
        frames = [
            pd.read_parquet(p, engine="pyarrow")
            for p in score_dir.glob("*.parquet")
            if p.is_file()
        ]
    else:
        files = list(selectors.iter_score_files(selection, data_type=data_type))
        frames = [selectors.read_parquet(p) for p in files]

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# data / trace
# ---------------------------------------------------------------------------

def save_raw_trace(
    df: pd.DataFrame,
    *,
    line_id: str,
    eqp_id: str,
    fdc_bin: str,
    dt: str,
    type: str,
    ppid: str,
    recipe_id: str,
    trace_param_name: str,
    filename: str = "data.parquet",
    data_root: str | Path | None = None,
) -> Path:
    """trace raw DataFrame 을 대시보드 파티션 경로에 저장합니다.

    Parameters
    ----------
    df:
        저장할 DataFrame. 최소 컬럼: ``날짜``, ``time``, ``step_time``, ``value``,
        ``trace_param_name``.
    dt:
        파티션 dt 값. YYYY-MM-DD 형식의 날짜 문자열.
    trace_param_name:
        센서 이름 (예: ``Pressure``, ``RF_Power``).

    Returns
    -------
    저장된 Parquet 파일의 절대 경로.
    """
    _check_required(df, _TRACE_REQUIRED, "data/trace")
    line_id = _validate_segment(line_id, "line_id")
    eqp_id = _validate_segment(eqp_id, "eqp_id")
    fdc_bin = _validate_segment(fdc_bin, "fdc_bin")
    dt = _validate_segment(dt, "dt")
    type = _validate_segment(type, "type")
    ppid = _validate_segment(ppid, "ppid")
    recipe_id = _validate_segment(recipe_id, "recipe_id")
    trace_param_name = _validate_segment(trace_param_name, "trace_param_name")

    root = Path(data_root).expanduser().resolve() if data_root else selectors.get_data_root()
    dest_dir = (
        root / selectors.RAW_DIR_NAME
        / f"line_id={line_id}"
        / f"eqp_id={eqp_id}"
        / f"fdc_bin={fdc_bin}"
        / f"dt={dt}"
        / f"type={type}"
        / f"ppid={ppid}"
        / f"recipe_id={recipe_id}"
        / "data_source=trace"
        / f"trace_param_name={trace_param_name}"
    )
    _make_dir(dest_dir)
    return _write_parquet(df, dest_dir / filename)


def load_raw_trace(
    *,
    line_id: str,
    eqp_id: str,
    type: str,
    fdc_bin: str | None = None,
    dt_values: Sequence[str] | None = None,
    ppid: str | None = None,
    recipe_id: str | None = None,
    trace_param_names: Sequence[str] | None = None,
    data_root: str | Path | None = None,
) -> pd.DataFrame:
    """save_raw_trace 로 저장한 파일을 읽어 하나의 DataFrame 으로 반환합니다.

    필터를 생략하면 와일드카드(*)로 처리되어 해당 파티션 전체를 읽습니다.
    """
    selection: dict[str, object] = {
        "lineId": line_id,
        "eqpId": eqp_id,
        "type": type,
        "fdcBin": fdc_bin or "",
        "ppid": ppid or "",
        "recipeId": recipe_id or "",
        "dtValues": list(dt_values or []),
    }
    if data_root:
        # Django settings 외부에서 호출할 때: selectors 의 get_data_root() 를
        # 우회해 직접 root 를 넘깁니다.
        import functools, types
        original_get = selectors.get_data_root
        selectors.get_data_root = lambda: Path(data_root).expanduser().resolve()
        try:
            files = list(selectors.iter_raw_files(
                selection, data_source="trace", trace_param_names=trace_param_names
            ))
        finally:
            selectors.get_data_root = original_get
    else:
        files = list(selectors.iter_raw_files(
            selection, data_source="trace", trace_param_names=trace_param_names
        ))

    if not files:
        return pd.DataFrame()
    frames = [selectors.read_parquet(p) for p in files]
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# data / OES
# ---------------------------------------------------------------------------

def save_raw_oes(
    df: pd.DataFrame,
    *,
    line_id: str,
    eqp_id: str,
    fdc_bin: str,
    dt: str,
    type: str,
    ppid: str,
    recipe_id: str,
    oes_group: str = "all",
    filename: str = "data.parquet",
    data_root: str | Path | None = None,
) -> Path:
    """OES raw DataFrame 을 대시보드 파티션 경로에 저장합니다.

    wide 형식(wavelength 가 컬럼명)과 long 형식(``wavelength``, ``value`` 컬럼 분리)
    모두 저장 가능합니다. 서비스가 자동으로 long 으로 변환합니다.

    Parameters
    ----------
    df:
        저장할 DataFrame.
        - long 형식: 최소 컬럼 ``날짜``, ``rcp_step``, ``wavelength``, ``value``
        - wide 형식: 최소 컬럼 ``날짜``, ``rcp_step`` + wavelength 컬럼(100~1200 nm)
    oes_group:
        trace_param_name 파티션에 들어갈 레이블. OES 파일끼리 구분이 필요하면
        step 이름 등을 사용하세요. 기본값 ``all``.

    Returns
    -------
    저장된 Parquet 파일의 절대 경로.
    """
    wide = _is_wide_oes(df)
    if not wide:
        _check_required(df, _OES_REQUIRED, "data/oes (long)")

    line_id = _validate_segment(line_id, "line_id")
    eqp_id = _validate_segment(eqp_id, "eqp_id")
    fdc_bin = _validate_segment(fdc_bin, "fdc_bin")
    dt = _validate_segment(dt, "dt")
    type = _validate_segment(type, "type")
    ppid = _validate_segment(ppid, "ppid")
    recipe_id = _validate_segment(recipe_id, "recipe_id")
    oes_group = _validate_segment(oes_group, "oes_group")

    root = Path(data_root).expanduser().resolve() if data_root else selectors.get_data_root()
    dest_dir = (
        root / selectors.RAW_DIR_NAME
        / f"line_id={line_id}"
        / f"eqp_id={eqp_id}"
        / f"fdc_bin={fdc_bin}"
        / f"dt={dt}"
        / f"type={type}"
        / f"ppid={ppid}"
        / f"recipe_id={recipe_id}"
        / "data_source=oes"
        / f"trace_param_name={oes_group}"
    )
    _make_dir(dest_dir)
    return _write_parquet(df, dest_dir / filename)


def load_raw_oes(
    *,
    line_id: str,
    eqp_id: str,
    type: str,
    fdc_bin: str | None = None,
    dt_values: Sequence[str] | None = None,
    ppid: str | None = None,
    recipe_id: str | None = None,
    data_root: str | Path | None = None,
) -> pd.DataFrame:
    """save_raw_oes 로 저장한 파일을 읽어 하나의 DataFrame 으로 반환합니다."""
    selection: dict[str, object] = {
        "lineId": line_id,
        "eqpId": eqp_id,
        "type": type,
        "fdcBin": fdc_bin or "",
        "ppid": ppid or "",
        "recipeId": recipe_id or "",
        "dtValues": list(dt_values or []),
    }
    if data_root:
        original_get = selectors.get_data_root
        selectors.get_data_root = lambda: Path(data_root).expanduser().resolve()
        try:
            files = list(selectors.iter_raw_files(selection, data_source="oes", trace_param_names=[]))
        finally:
            selectors.get_data_root = original_get
    else:
        files = list(selectors.iter_raw_files(selection, data_source="oes", trace_param_names=[]))

    if not files:
        return pd.DataFrame()
    frames = [selectors.read_parquet(p) for p in files]
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# 편의 함수
# ---------------------------------------------------------------------------

def list_partitions(
    dataset: str = selectors.RAW_DIR_NAME,
    data_root: str | Path | None = None,
) -> list[dict[str, str]]:
    """저장된 파티션 목록을 반환합니다.

    Parameters
    ----------
    dataset:
        ``data`` 또는 ``result``.

    Returns
    -------
    각 리프 디렉터리의 파티션 key=value 를 dict 로 모은 목록.
    """
    root = Path(data_root).expanduser().resolve() if data_root else selectors.get_data_root()
    dataset_root = root / dataset
    if not dataset_root.is_dir():
        return []
    results: list[dict[str, str]] = []
    for parquet_file in sorted(dataset_root.rglob("*.parquet")):
        partition = selectors.parse_partition_values(parquet_file.parent)
        if partition:
            results.append(partition)
    return results


def verify_score(
    df: pd.DataFrame,
    *,
    line_id: str,
    eqp_id: str,
    chamber_id: str,
    type: str,
    data_type: str,
    data_root: str | Path | None = None,
) -> dict[str, object]:
    """score DataFrame 을 저장한 뒤 다시 읽어 저장 결과를 검증합니다.

    Returns
    -------
    ``{"path": ..., "rows_written": ..., "rows_read": ..., "ok": bool}``
    """
    path = save_score(
        df,
        line_id=line_id, eqp_id=eqp_id, chamber_id=chamber_id,
        type=type, data_type=data_type,
        data_root=data_root,
    )
    loaded = load_score(
        line_id=line_id, eqp_id=eqp_id, chamber_id=chamber_id,
        type=type, data_type=data_type,
        data_root=data_root,
    )
    return {
        "path": path,
        "rows_written": len(df),
        "rows_read": len(loaded),
        "ok": len(loaded) >= len(df),
    }
