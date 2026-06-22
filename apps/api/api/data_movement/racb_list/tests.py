"""racb_list 적재 앱 테스트입니다."""

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

from api.data_movement.racb_list.management.commands.load_racb_list import services
from api.data_movement.racb_list.models import RacbList, RacbListLoadJob
from api.data_movement.racb_list import selectors
from api.data_movement.racb_list.services import loader as loader_module
from api.data_movement.racb_list.services import spec
from api.data_movement.racb_list.services.loader import LoadFileOutcome, LoadRunSummary


def _write_deflate_csv(path: Path, rows: list[list[str]]) -> None:
    """테스트용 racb_list deflate CSV 파일을 생성합니다."""

    buffer = StringIO()
    import csv

    writer = csv.writer(buffer, delimiter=spec.FILE_SEPARATOR)
    writer.writerows(rows)
    path.write_bytes(zlib.compress(buffer.getvalue().encode("utf-8")))


def _build_racb_row(
    *,
    c_racb_id: str = "RACB-1",
    title: str = "RACB title",
    racb_type_cd: str = "ALARM",
    eqp_ids: str = "EAAA301-A, EAAA301-B",
    create_date: str = "2026-06-20 10:00:00",
    update_date: str = "2026-06-20 10:05:00",
    user_name: str = "USER01",
    line_id: str = "LINE-A",
) -> list[str]:
    """spec 컬럼 순서에 맞춘 테스트용 RACB row를 생성합니다."""

    return [
        c_racb_id,
        "ORACB-1",
        "GBM",
        "LINE",
        line_id,
        "AREA",
        "SDWT",
        title,
        "SUB",
        "FIVEONE",
        racb_type_cd,
        "MAJOR",
        "MINOR",
        eqp_ids,
        "PRC",
        "LEVEL",
        "100",
        "OPEN",
        "DETAIL",
        "CHANGE",
        "Y",
        "N",
        "N",
        "N",
        create_date,
        "2026-06-30 00:00:00",
        user_name,
        "CREATOR",
        update_date,
        "UPDATER",
        "SUBAREA",
    ]


class RacbListStructureTests(SimpleTestCase):
    """racb_list 앱 구조와 command 경계를 검증합니다."""

    def test_model_table_names_match_expected_tables(self) -> None:
        """모델의 실제 DB 테이블명이 합의한 이름과 일치하는지 확인합니다."""

        self.assertEqual(RacbList._meta.db_table, "racb_list")
        self.assertEqual(RacbListLoadJob._meta.db_table, "racb_list_load_job")

    def test_model_indexes_support_timeline_query(self) -> None:
        """EQP-CB별 시간 범위 조회용 복합 인덱스가 있는지 확인합니다."""

        index_names = {index.name for index in RacbList._meta.indexes}
        constraint_names = {constraint.name for constraint in RacbList._meta.constraints}

        self.assertIn("idx_racb_list_cb_upd", index_names)
        self.assertIn("idx_racb_list_upd", index_names)
        self.assertIn("uniq_racb_list_id_cb", constraint_names)

    @patch.object(services, "load_racb_list_files")
    def test_command_reports_no_files(self, load_files) -> None:
        """처리 파일이 없으면 성공 메시지만 출력하는지 확인합니다."""

        load_files.return_value = LoadRunSummary(outcomes=[])
        stdout = StringIO()

        call_command("load_racb_list", stdout=stdout)

        self.assertIn("처리할 파일 없음", stdout.getvalue())

    @patch.object(services, "load_racb_list_files")
    def test_command_raises_when_any_file_failed(self, load_files) -> None:
        """실패 파일이 하나라도 있으면 Airflow가 실패를 감지하도록 예외를 발생시킵니다."""

        load_files.return_value = LoadRunSummary(
            outcomes=[
                LoadFileOutcome(
                    file_name="bad.csv.deflate",
                    status=RacbListLoadJob.Status.FAILED,
                    row_count=0,
                    error_message="invalid",
                )
            ]
        )

        with self.assertRaises(CommandError):
            call_command("load_racb_list", stdout=StringIO())


@override_settings(DATA_MOVEMENT_FILE_READY_MIN_AGE_SECONDS=0, DATA_MOVEMENT_FILE_READY_STABILITY_SECONDS=0)
class RacbListLifecycleTests(TestCase):
    """RACB 이력 파일 처리 lifecycle을 검증합니다."""

    def test_loader_keeps_latest_racb_and_explodes_eqp_ids(self) -> None:
        """c_racb_id별 최신 row만 남긴 뒤 eqp_ids를 설비별 row로 분리합니다."""

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            incoming = root / "incoming"
            incoming.mkdir()
            source = incoming / "sample_racb_list_20260620.csv.deflate"
            _write_deflate_csv(
                source,
                [
                    spec.FILE_COLUMNS,
                    _build_racb_row(
                        c_racb_id="RACB-1",
                        title="old title",
                        eqp_ids="EOLD301-A",
                        update_date="2026-06-20 09:00:00",
                    ),
                    _build_racb_row(
                        c_racb_id="RACB-1",
                        title="new title",
                        eqp_ids="EAAA301-A, EAAA301-B",
                        update_date="2026-06-20 10:05:00",
                    ),
                    _build_racb_row(
                        c_racb_id="RACB-2",
                        title="warn title",
                        racb_type_cd="WARN",
                        eqp_ids="EBBB302-A",
                    ),
                    _build_racb_row(
                        c_racb_id="",
                        title="missing id",
                        eqp_ids="ESKIP301-A",
                    ),
                ],
            )

            summary = loader_module.load_racb_list_files(data_dir=root)

        self.assertEqual(summary.success_count, 1, summary.outcomes)
        self.assertEqual(RacbList.objects.count(), 3)
        self.assertFalse(RacbList.objects.filter(eqp_cb="EOLD301-A").exists())
        self.assertTrue(RacbList.objects.filter(c_racb_id="RACB-1", eqp_cb="EAAA301-A", title="new title").exists())
        self.assertTrue(RacbList.objects.filter(c_racb_id="RACB-1", eqp_cb="EAAA301-B", title="new title").exists())
        self.assertTrue(RacbList.objects.filter(c_racb_id="RACB-2", eqp_cb="EBBB302-A", racb_type_cd="WARN").exists())

    def test_loader_replaces_existing_rows_for_source_racb_ids(self) -> None:
        """같은 c_racb_id가 다시 들어오면 이전 explode 결과를 제거하고 새 결과만 저장합니다."""

        RacbList.objects.create(
            c_racb_id="RACB-1",
            eqp_cb="EOLD301-A",
            line_id="LINE-A",
            create_date=datetime(2026, 6, 20, 8, 0, tzinfo=datetime_timezone.utc),
            update_date=datetime(2026, 6, 20, 8, 5, tzinfo=datetime_timezone.utc),
        )

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            incoming = root / "incoming"
            incoming.mkdir()
            source = incoming / "sample_racb_list_20260620.csv.deflate"
            _write_deflate_csv(
                source,
                [
                    spec.FILE_COLUMNS,
                    _build_racb_row(
                        c_racb_id="RACB-1",
                        title="replacement",
                        eqp_ids="ENEW301-A",
                    ),
                ],
            )

            summary = loader_module.load_racb_list_files(data_dir=root)

        self.assertEqual(summary.success_count, 1, summary.outcomes)
        self.assertFalse(RacbList.objects.filter(eqp_cb="EOLD301-A").exists())
        self.assertTrue(RacbList.objects.filter(eqp_cb="ENEW301-A", title="replacement").exists())

    def test_selector_returns_observer_racb_payload(self) -> None:
        """내부 테이블 row를 observer RACB payload로 변환합니다."""

        RacbList.objects.create(
            c_racb_id="RACB-1",
            eqp_cb="EAAA301-A",
            line_id="LINE-A",
            title="RACB title",
            racb_type_cd="ALARM",
            status_code="OPEN",
            user_name="USER01",
            create_date=datetime(2026, 6, 20, 10, 0, tzinfo=datetime_timezone.utc),
            update_date=datetime(2026, 6, 20, 10, 5, tzinfo=datetime_timezone.utc),
        )

        logs = selectors.fetch_racb_timeline_logs(
            eqp_id="eaaa301-a",
            start_at="2026-06-01T00:00:00",
            limit=10,
        )

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["id"], "RACB-RACB-1-EAAA301-A")
        self.assertEqual(logs[0]["eqpId"], "EAAA301-A")
        self.assertEqual(logs[0]["logType"], "RACB")
        self.assertEqual(logs[0]["eventType"], "ALARM_OPEN")
        self.assertEqual(logs[0]["eventTime"], datetime(2026, 6, 20, 10, 5, tzinfo=datetime_timezone.utc))
        self.assertEqual(logs[0]["operator"], "USER01")
        self.assertEqual(logs[0]["comment"], "RACB title")
        self.assertEqual(
            logs[0]["url"],
            "https://racb.eqms.abc.net/racb/rpt/ReportPop.do?racbId=RACB-1&lineId=LINE-A",
        )
