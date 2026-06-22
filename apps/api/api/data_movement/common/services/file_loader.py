"""파일 기반 적재 대상 목록과 lifecycle을 관리하는 공통 헬퍼입니다."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path
from uuid import uuid4

from django.conf import settings


NANOSECONDS_PER_SECOND = 1_000_000_000


@dataclass(frozen=True)
class DataMovementDirs:
    """테이블별 data movement 디렉터리 묶음입니다."""

    root: Path
    incoming: Path
    processing: Path


@dataclass(frozen=True)
class ClaimedDataFile:
    """처리 대상으로 선점한 파일 정보입니다."""

    original_path: Path
    working_path: Path
    original_name: str


@dataclass(frozen=True)
class DataFileSnapshot:
    """파일 완료 여부 판단에 사용하는 stat 값입니다."""

    size: int
    mtime_ns: int


def get_data_movement_dirs(*, table_dir: Path) -> DataMovementDirs:
    """테이블별 표준 lifecycle 디렉터리 경로를 반환합니다."""

    return DataMovementDirs(
        root=table_dir,
        incoming=table_dir / "incoming",
        processing=table_dir / "processing",
    )


def ensure_data_movement_dirs(*, dirs: DataMovementDirs) -> None:
    """표준 lifecycle 디렉터리를 생성합니다."""

    for path in (dirs.incoming, dirs.processing):
        path.mkdir(parents=True, exist_ok=True)


def _get_non_negative_int_setting(*, name: str, default: int) -> int:
    """음수 설정값은 0으로 보정해 readiness 계산을 단순화합니다."""

    value = getattr(settings, name, default)
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(parsed, 0)


def _get_file_snapshot(*, file_path: Path) -> DataFileSnapshot | None:
    """파일이 사라진 경우 readiness 후보에서 제외할 수 있게 None을 반환합니다."""

    try:
        stat_result = file_path.stat()
    except FileNotFoundError:
        return None
    return DataFileSnapshot(size=stat_result.st_size, mtime_ns=stat_result.st_mtime_ns)


def _is_min_age_satisfied(*, snapshot: DataFileSnapshot, now_ns: int, min_age_seconds: int) -> bool:
    """파일 수정 시각이 최소 안정화 시간을 지났는지 확인합니다."""

    if min_age_seconds <= 0:
        return True
    return now_ns - snapshot.mtime_ns >= min_age_seconds * NANOSECONDS_PER_SECOND


def _filter_ready_files(*, files: list[Path]) -> list[Path]:
    """최근 수정 파일과 stat 값이 변하는 파일을 적재 후보에서 제외합니다."""

    min_age_seconds = _get_non_negative_int_setting(
        name="DATA_MOVEMENT_FILE_READY_MIN_AGE_SECONDS",
        default=60,
    )
    stability_seconds = _get_non_negative_int_setting(
        name="DATA_MOVEMENT_FILE_READY_STABILITY_SECONDS",
        default=1,
    )
    now_ns = time.time_ns()
    snapshots: dict[Path, DataFileSnapshot] = {}
    for file_path in files:
        snapshot = _get_file_snapshot(file_path=file_path)
        if snapshot is None:
            continue
        if not _is_min_age_satisfied(
            snapshot=snapshot,
            now_ns=now_ns,
            min_age_seconds=min_age_seconds,
        ):
            continue
        snapshots[file_path] = snapshot

    if stability_seconds > 0 and snapshots:
        time.sleep(stability_seconds)
        snapshots = {
            file_path: snapshot
            for file_path, snapshot in snapshots.items()
            if _get_file_snapshot(file_path=file_path) == snapshot
        }

    return [file_path for file_path in files if file_path in snapshots]


def list_data_files(
    *,
    data_dir: Path,
    pattern: str,
    limit: int | None = None,
    require_ready: bool = False,
) -> list[Path]:
    """지정 경로에서 적재 대상 파일을 대소문자 구분 없이 이름순으로 반환합니다."""

    if limit is not None and limit < 1:
        raise ValueError("limit은 1 이상이어야 합니다.")

    if not data_dir.exists():
        return []
    if not data_dir.is_dir():
        raise NotADirectoryError(f"적재 경로가 디렉터리가 아닙니다: {data_dir}")

    normalized_pattern = pattern.casefold()
    files = sorted(
        (
            path
            for path in data_dir.iterdir()
            if path.is_file() and fnmatchcase(path.name.casefold(), normalized_pattern)
        ),
        key=lambda path: path.name.casefold(),
    )
    if require_ready:
        files = _filter_ready_files(files=files)
    if limit is None:
        return files
    return files[:limit]


def list_incoming_files(*, table_dir: Path, pattern: str, limit: int | None = None) -> list[Path]:
    """테이블 root의 incoming 디렉터리에서 완료 파일만 반환합니다."""

    dirs = get_data_movement_dirs(table_dir=table_dir)
    ensure_data_movement_dirs(dirs=dirs)
    return list_data_files(data_dir=dirs.incoming, pattern=pattern, limit=limit, require_ready=True)


def claim_incoming_file(*, file_path: Path, table_dir: Path) -> ClaimedDataFile:
    """incoming 파일을 processing으로 atomic move하여 처리 대상으로 선점합니다."""

    dirs = get_data_movement_dirs(table_dir=table_dir)
    ensure_data_movement_dirs(dirs=dirs)
    working_name = f"{file_path.stem}.{os.getpid()}.{uuid4().hex}{file_path.suffix}"
    working_path = dirs.processing / working_name
    file_path.replace(working_path)
    return ClaimedDataFile(
        original_path=file_path,
        working_path=working_path,
        original_name=file_path.name,
    )


def delete_claimed_file(*, claimed_file: ClaimedDataFile) -> None:
    """선점 파일이 남아 있으면 삭제합니다."""

    try:
        claimed_file.working_path.unlink()
    except FileNotFoundError:
        return
