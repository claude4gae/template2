"""파일 기반 적재 대상 목록과 lifecycle을 관리하는 공통 헬퍼입니다."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4


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


def list_data_files(*, data_dir: Path, pattern: str, limit: int | None = None) -> list[Path]:
    """지정 경로에서 적재 대상 파일을 이름순으로 반환합니다."""

    if limit is not None and limit < 1:
        raise ValueError("limit은 1 이상이어야 합니다.")

    if not data_dir.exists():
        return []
    if not data_dir.is_dir():
        raise NotADirectoryError(f"적재 경로가 디렉터리가 아닙니다: {data_dir}")

    files = sorted(path for path in data_dir.glob(pattern) if path.is_file())
    if limit is None:
        return files
    return files[:limit]


def list_incoming_files(*, table_dir: Path, pattern: str, limit: int | None = None) -> list[Path]:
    """테이블 root의 incoming 디렉터리에서 완료 파일만 반환합니다."""

    dirs = get_data_movement_dirs(table_dir=table_dir)
    ensure_data_movement_dirs(dirs=dirs)
    return list_data_files(data_dir=dirs.incoming, pattern=pattern, limit=limit)


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
