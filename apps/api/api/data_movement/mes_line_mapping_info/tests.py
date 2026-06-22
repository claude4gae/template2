"""mes_line_mapping_info 적재 앱 테스트입니다."""

from __future__ import annotations

import zlib
from datetime import datetime, timezone as datetime_timezone
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, override_settings

from api.data_movement.common.services.postgres_copy import CopyFullReplaceResult
from api.data_movement.mes_line_mapping_info.management.commands.load_mes_line_mapping_info import services
from api.data_movement.mes_line_mapping_info.models import (
    MesLineMappingInfo,
    MesLineMappingInfoLoadJob,
)
from api.data_movement.mes_line_mapping_info.services import loader as loader_module
from api.data_movement.mes_line_mapping_info.services import spec
from api.data_movement.mes_line_mapping_info.services.loader import LoadFileOutcome, LoadRunSummary


def _write_deflate_mapping_csv(path: Path, rows: list[list[str]]) -> None:
    """테스트용 mes_line_mapping_info deflate CSV 파일을 생성합니다."""

    payload = "\n".join(spec.FILE_SEPARATOR.join(row) for row in rows).encode("utf-8")
    path.write_bytes(zlib.compress(payload))


def _build_mapping_row(*, seq_no: str = "1", line_id: str = "L1", gpm_line_name: str = "GPM-L1") -> list[str]:
    """spec 컬럼 순서에 맞춘 테스트용 mes_line_mapping_info row를 생성합니다."""

    row = [""] * len(spec.COLUMNS)
    row[0] = seq_no
    row[1] = line_id
    row[2] = "MOS1"
    row[3] = "FDC1"
    row[4] = gpm_line_name
    row[6] = "MSG1"
    row[10] = "MEMORY"
    row[20] = "2"
    row[21] = "Y"
    row[22] = "N"
    row[23] = "2026-06-19 10:20:30"
    row[25] = "2026-06-19 11:20:30"
    return row


class MesLineMappingInfoStructureTests(SimpleTestCase):
    """mes_line_mapping_info 앱 구조와 command 경계를 검증합니다."""

    def test_model_table_names_match_expected_tables(self) -> None:
        """모델의 실제 DB 테이블명이 합의한 이름과 일치하는지 확인합니다."""

        self.assertEqual(MesLineMappingInfo._meta.db_table, "mes_line_mapping_info")
        self.assertEqual(MesLineMappingInfoLoadJob._meta.db_table, "mes_line_mapping_info_load_job")

    @patch.object(services, "load_mes_line_mapping_info_files")
    def test_command_reports_no_files(self, load_files) -> None:
        """처리 파일이 없으면 성공 메시지만 출력하는지 확인합니다."""

        load_files.return_value = LoadRunSummary(outcomes=[])
        stdout = StringIO()

        call_command("load_mes_line_mapping_info", stdout=stdout)

        self.assertIn("처리할 파일 없음", stdout.getvalue())

    @patch.object(services, "load_mes_line_mapping_info_files")
    def test_command_raises_when_any_file_failed(self, load_files) -> None:
        """실패 파일이 하나라도 있으면 Airflow가 실패를 감지하도록 예외를 발생시킵니다."""

        load_files.return_value = LoadRunSummary(
            outcomes=[
                LoadFileOutcome(
                    file_name="bad.csv.deflate",
                    status=MesLineMappingInfoLoadJob.Status.FAILED,
                    row_count=0,
                    error_message="broken file",
                )
            ]
        )

        with self.assertRaises(CommandError):
            call_command("load_mes_line_mapping_info", stdout=StringIO())

    def test_read_mapping_frame_accepts_timezone_aware_update_date(self) -> None:
        """timezone offset이 포함된 update_date를 UTC datetime으로 변환합니다."""

        with TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "86114_MES_LINE_MAPPING_INFO_20260619.csv.deflate"
            row = _build_mapping_row()
            row[25] = "2026-06-19 11:20:30+09:00"
            _write_deflate_mapping_csv(source, [row])

            frame = loader_module._read_mapping_frame(file_path=source)

        update_date = frame.select("update_date").to_series().to_list()[0]
        self.assertEqual(update_date, datetime(2026, 6, 19, 2, 20, 30, tzinfo=datetime_timezone.utc))


@override_settings(DATA_MOVEMENT_FILE_READY_MIN_AGE_SECONDS=0, DATA_MOVEMENT_FILE_READY_STABILITY_SECONDS=0)
class MesLineMappingInfoLifecycleTests(TestCase):
    """MES 매핑 수신 파일과 loader 처리 파일의 생명주기를 검증합니다."""

    def test_loader_replaces_all_rows_in_database(self) -> None:
        """실제 COPY 경로로 기존 전체 row를 새 파일 내용으로 교체합니다."""

        MesLineMappingInfo.objects.create(seq_no=99, line_id="OLD_LINE")

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            incoming = root / "incoming"
            incoming.mkdir()
            source = incoming / "86114_MES_LINE_MAPPING_INFO_20260619.csv.deflate"
            _write_deflate_mapping_csv(
                source,
                [
                    _build_mapping_row(seq_no="1", line_id="L1", gpm_line_name="GPM-L1"),
                    _build_mapping_row(seq_no="2", line_id="L2", gpm_line_name="GPM-L2"),
                ],
            )

            summary = loader_module.load_mes_line_mapping_info_files(data_dir=root)

        self.assertEqual(summary.success_count, 1)
        self.assertFalse(MesLineMappingInfo.objects.filter(line_id="OLD_LINE").exists())
        self.assertEqual(MesLineMappingInfo.objects.count(), 2)
        loaded_row = MesLineMappingInfo.objects.get(line_id="L1")
        self.assertEqual(loaded_row.line_id, "L1")
        self.assertEqual(loaded_row.gpm_line_name, "GPM-L1")
        self.assertEqual(loaded_row.gbm_name, "MEMORY")
        self.assertEqual(loaded_row.use_yn, "Y")
        self.assertEqual(loaded_row.del_yn, "N")
        self.assertEqual(loaded_row.seq_no, 1)
        self.assertEqual(loaded_row.sort_seq, 2)
        self.assertIsNotNone(loaded_row.create_date)

    @patch.object(loader_module, "copy_full_replace_rows")
    @patch.object(loader_module, "_read_mapping_frame")
    def test_loader_claims_incoming_file_and_deletes_on_success(
        self,
        read_file,
        copy_rows,
    ) -> None:
        """성공 시 incoming 파일을 processing 경유 삭제합니다."""

        read_file.return_value = type("Frame", (), {"shape": (1, len(spec.COLUMNS))})()
        copy_rows.return_value = CopyFullReplaceResult(row_count=1, column_count=len(spec.COLUMNS))

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            incoming = root / "incoming"
            incoming.mkdir()
            source = incoming / "86114_MES_LINE_MAPPING_INFO_20260619.csv.deflate"
            source.write_text("payload", encoding="utf-8")

            summary = loader_module.load_mes_line_mapping_info_files(data_dir=root)

            self.assertEqual(summary.success_count, 1)
            self.assertFalse(source.exists())
            self.assertFalse((root / "archive").exists())
            self.assertFalse((root / "error").exists())
            self.assertEqual(list((root / "processing").iterdir()), [])

        self.assertEqual(
            MesLineMappingInfoLoadJob.objects.filter(status=MesLineMappingInfoLoadJob.Status.SUCCESS).count(),
            1,
        )

    @patch.object(loader_module, "_read_mapping_frame")
    def test_loader_deletes_failed_file(self, read_file) -> None:
        """처리 실패 시 선점 파일도 삭제합니다."""

        read_file.side_effect = ValueError("broken file")

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            incoming = root / "incoming"
            incoming.mkdir()
            source = incoming / "86114_MES_LINE_MAPPING_INFO_20260619.csv.deflate"
            source.write_text("payload", encoding="utf-8")

            summary = loader_module.load_mes_line_mapping_info_files(data_dir=root)

            self.assertEqual(summary.failure_count, 1)
            self.assertFalse(source.exists())
            self.assertFalse((root / "archive").exists())
            self.assertFalse((root / "error").exists())
            self.assertEqual(list((root / "processing").iterdir()), [])

        self.assertEqual(
            MesLineMappingInfoLoadJob.objects.filter(status=MesLineMappingInfoLoadJob.Status.FAILED).count(),
            1,
        )
