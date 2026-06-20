"""ct_process_comment 적재 앱 테스트입니다."""

from __future__ import annotations

import zlib
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import SimpleTestCase, TestCase

from api.data_movement.common.services.streaming_csv import write_selected_deflate_csv
from api.data_movement.ct_process_comment.management.commands.load_ct_process_comment import services
from api.data_movement.ct_process_comment.models import CtProcessComment, CtProcessCommentLoadJob
from api.data_movement.ct_process_comment.services import loader as loader_module
from api.data_movement.ct_process_comment.services import spec
from api.data_movement.ct_process_comment.services.loader import LoadFileOutcome, LoadRunSummary


def _write_deflate_csv(path: Path, rows: list[list[str]]) -> None:
    """테스트용 deflate CSV 파일을 생성합니다."""

    payload = "\n".join(spec.FILE_SEPARATOR.join(row) for row in rows).encode("utf-8")
    path.write_bytes(zlib.compress(payload))


def _build_comment_row(
    *,
    workorder_id: str = "WO1",
    line_id: str = "L1",
    eqp_id: str = "EQP1",
    contents: str = "contents",
    use_yn: str = "Y",
    create_date: str = "2999-01-01 00:00:00",
    update_date: str | None = None,
) -> list[str]:
    """DDL 순서에 맞춘 테스트용 comment row를 생성합니다."""

    row = [""] * len(spec.FILE_COLUMNS)
    row[0] = workorder_id
    row[1] = line_id
    row[2] = "PROC"
    row[3] = "1"
    row[4] = "C1"
    row[5] = eqp_id
    row[6] = "N"
    row[7] = contents
    row[8] = "contents text"
    row[9] = create_date
    row[10] = "creator"
    row[11] = update_date or create_date
    row[12] = "updater"
    row[13] = use_yn
    row[14] = "modifier"
    row[15] = create_date
    row[16] = "part"
    return row


class CtProcessCommentStructureTests(SimpleTestCase):
    """ct_process_comment 앱 구조와 파일 spec을 검증합니다."""

    def test_model_table_names_match_expected_tables(self) -> None:
        """모델의 실제 DB 테이블명이 합의한 이름과 일치하는지 확인합니다."""

        self.assertEqual(CtProcessComment._meta.db_table, "ct_process_comment")
        self.assertEqual(CtProcessCommentLoadJob._meta.db_table, "ct_process_comment_load_job")

    def test_model_has_llm_summary_field(self) -> None:
        """contents_text의 LLM 요약 결과를 저장할 컬럼이 있는지 확인합니다."""

        field = CtProcessComment._meta.get_field("llm_summary")

        self.assertTrue(field.null)
        self.assertTrue(field.blank)

    def test_parse_source_file_name_extracts_timestamp(self) -> None:
        """파일명에서 timestamp를 추출하는지 확인합니다."""

        info = loader_module.parse_source_file_name(file_name="65635_CT_PROCESS_COMMENT_20260529_1300.csv.deflate")

        self.assertEqual(info.file_timestamp, "20260529_1300")

    def test_parse_source_file_name_ignores_file_name_case(self) -> None:
        """파일명 대소문자가 달라도 timestamp를 추출합니다."""

        info = loader_module.parse_source_file_name(file_name="65635_ct_process_comment_20260529_1300.CSV.DEFLATE")

        self.assertEqual(info.file_timestamp, "20260529_1300")

    def test_write_selected_deflate_csv_filters_use_yn_and_eqp_prefix(self) -> None:
        """USE_YN=N 행과 EQP_ID가 E/e로 시작하지 않는 행을 제외합니다."""

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.csv.deflate"
            selected = root / "selected.csv"
            _write_deflate_csv(
                source,
                [
                    _build_comment_row(workorder_id="WO1", use_yn="Y"),
                    _build_comment_row(workorder_id="WO2", use_yn="N"),
                    _build_comment_row(
                        workorder_id="WO3",
                        eqp_id="eQP2",
                        use_yn="Y",
                        create_date="2000-01-01 00:00:00",
                    ),
                    _build_comment_row(workorder_id="WO4", eqp_id="AQP1", use_yn="Y"),
                ],
            )

            row_count = write_selected_deflate_csv(
                source_path=source,
                output_path=selected,
                file_columns=spec.FILE_COLUMNS,
                db_columns=spec.DB_COLUMNS,
                excluded_row_filters=spec.EXCLUDED_ROW_FILTERS,
                prefix_row_filters=spec.PREFIX_ROW_FILTERS,
                separator=spec.FILE_SEPARATOR,
            )

            self.assertEqual(row_count, 2)
            selected_rows = selected.read_text(encoding="utf-8").splitlines()
            self.assertTrue(selected_rows[0].startswith("WO1,L1,PROC"))
            self.assertTrue(selected_rows[1].startswith("WO3,L1,PROC"))

    @patch.object(services, "load_ct_process_comment_files")
    def test_command_reports_no_files(self, load_files) -> None:
        """처리 파일이 없으면 성공 메시지만 출력하는지 확인합니다."""

        load_files.return_value = LoadRunSummary(outcomes=[])
        stdout = StringIO()

        call_command("load_ct_process_comment", stdout=stdout)

        self.assertIn("처리할 파일 없음", stdout.getvalue())

    @patch.object(services, "load_ct_process_comment_files")
    def test_command_raises_when_any_file_failed(self, load_files) -> None:
        """실패 파일이 하나라도 있으면 Airflow가 실패를 감지하도록 예외를 발생시킵니다."""

        load_files.return_value = LoadRunSummary(
            outcomes=[
                LoadFileOutcome(
                    file_name="bad.csv.deflate",
                    status=CtProcessCommentLoadJob.Status.FAILED,
                    row_count=0,
                    error_message="invalid",
                )
            ]
        )

        with self.assertRaises(CommandError):
            call_command("load_ct_process_comment", stdout=StringIO())


class CtProcessCommentLifecycleTests(TestCase):
    """CT_PROCESS_COMMENT 파일 처리 lifecycle을 검증합니다."""

    def test_loader_upserts_existing_workorder_comment_in_database(self) -> None:
        """실제 COPY 경로로 기존 workorder comment를 새 파일 row로 갱신합니다."""

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO ctttm_workorder_list
                    (source_type, workorder_id, line_id, eqp_id, work_type, description, inprg_date, comp_date)
                VALUES
                    ('MST', 'WO1', 'L1', 'EQP1', 'PM', 'desc', NULL, NULL),
                    ('MST', 'WO2', 'L1', 'eQP2', 'PM', 'desc', NULL, NULL)
                """
            )
        CtProcessComment.objects.create(
            workorder_id="WO1",
            line_id="OLD_LINE",
            contents="old contents",
            use_yn="Y",
        )

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            incoming = root / "incoming"
            incoming.mkdir()
            source = incoming / "65635_CT_PROCESS_COMMENT_20260529_1300.csv.deflate"
            _write_deflate_csv(
                source,
                [
                    _build_comment_row(workorder_id="WO1", line_id="NEW_LINE", contents="new contents"),
                    _build_comment_row(workorder_id="WO2", eqp_id="eQP2", contents="created contents"),
                    _build_comment_row(workorder_id="WO_MISSING", line_id="SKIP_LINE", contents="skip contents"),
                ],
            )

            summary = loader_module.load_ct_process_comment_files(data_dir=root)

        self.assertEqual(summary.success_count, 1)
        updated_row = CtProcessComment.objects.get(workorder_id="WO1")
        self.assertEqual(updated_row.line_id, "NEW_LINE")
        self.assertEqual(updated_row.contents, "new contents")
        self.assertEqual(updated_row.update_flag, "Y")
        created_row = CtProcessComment.objects.get(workorder_id="WO2")
        self.assertEqual(created_row.contents, "created contents")
        self.assertEqual(created_row.update_flag, "Y")
        self.assertFalse(CtProcessComment.objects.filter(workorder_id="WO_MISSING").exists())

    def test_loader_keeps_one_latest_row_when_file_has_duplicate_workorder_id(self) -> None:
        """같은 파일의 중복 workorder_id는 최신 update_date row 하나만 반영합니다."""

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO ctttm_workorder_list
                    (source_type, workorder_id, line_id, eqp_id, work_type, description, inprg_date, comp_date)
                VALUES
                    ('MST', 'WO1', 'L1', 'EQP1', 'PM', 'desc', NULL, NULL)
                """
            )

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            incoming = root / "incoming"
            incoming.mkdir()
            source = incoming / "65635_CT_PROCESS_COMMENT_20260529_1300.csv.deflate"
            _write_deflate_csv(
                source,
                [
                    _build_comment_row(
                        workorder_id="WO1",
                        line_id="OLD_LINE",
                        contents="old contents",
                        update_date="2999-01-01 00:00:00",
                    ),
                    _build_comment_row(
                        workorder_id="WO1",
                        line_id="NEW_LINE",
                        contents="new contents",
                        update_date="2999-01-02 00:00:00",
                    ),
                ],
            )

            summary = loader_module.load_ct_process_comment_files(data_dir=root)

        self.assertEqual(summary.success_count, 1, summary.outcomes)
        self.assertEqual(CtProcessComment.objects.filter(workorder_id="WO1").count(), 1)
        loaded_row = CtProcessComment.objects.get(workorder_id="WO1")
        self.assertEqual(loaded_row.line_id, "NEW_LINE")
        self.assertEqual(loaded_row.contents, "new contents")

    def test_loader_keeps_update_flag_when_existing_comment_is_unchanged(self) -> None:
        """동일한 comment row 재적재는 API 요청 flag를 새로 켜지 않습니다."""

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO ctttm_workorder_list
                    (source_type, workorder_id, line_id, eqp_id, work_type, description, inprg_date, comp_date)
                VALUES
                    ('MST', 'WO1', 'L1', 'EQP1', 'PM', 'desc', NULL, NULL)
                """
            )

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            incoming = root / "incoming"
            incoming.mkdir()
            source = incoming / "65635_CT_PROCESS_COMMENT_20260529_1300.csv.deflate"
            _write_deflate_csv(source, [_build_comment_row(workorder_id="WO1")])

            first_summary = loader_module.load_ct_process_comment_files(data_dir=root)

            self.assertEqual(first_summary.success_count, 1)
            loaded_row = CtProcessComment.objects.get(workorder_id="WO1")
            self.assertEqual(loaded_row.update_flag, "Y")

            loaded_row.update_flag = "N"
            loaded_row.save(update_fields=["update_flag"])
            source = incoming / "65635_CT_PROCESS_COMMENT_20260529_1400.csv.deflate"
            _write_deflate_csv(source, [_build_comment_row(workorder_id="WO1")])

            second_summary = loader_module.load_ct_process_comment_files(data_dir=root)

        self.assertEqual(second_summary.success_count, 1, second_summary.outcomes)
        unchanged_row = CtProcessComment.objects.get(workorder_id="WO1")
        self.assertEqual(unchanged_row.update_flag, "N")

    def test_loader_resets_llm_summary_when_contents_text_changes(self) -> None:
        """contents_text 변경 시 기존 LLM 요약을 비워 재요약 대상이 되게 합니다."""

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO ctttm_workorder_list
                    (source_type, workorder_id, line_id, eqp_id, work_type, description, inprg_date, comp_date)
                VALUES
                    ('MST', 'WO1', 'L1', 'EQP1', 'PM', 'desc', NULL, NULL)
                """
            )
        CtProcessComment.objects.create(
            workorder_id="WO1",
            line_id="OLD_LINE",
            contents_text="old text",
            llm_summary="old summary",
            use_yn="Y",
        )

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            incoming = root / "incoming"
            incoming.mkdir()
            source = incoming / "65635_CT_PROCESS_COMMENT_20260529_1300.csv.deflate"
            _write_deflate_csv(source, [_build_comment_row(workorder_id="WO1")])

            summary = loader_module.load_ct_process_comment_files(data_dir=root)

        self.assertEqual(summary.success_count, 1, summary.outcomes)
        updated_row = CtProcessComment.objects.get(workorder_id="WO1")
        self.assertEqual(updated_row.contents_text, "contents text")
        self.assertIsNone(updated_row.llm_summary)

    @patch.object(loader_module, "_upsert_rows")
    def test_loader_upserts_and_deletes_processing_file(self, upsert_rows) -> None:
        """성공 시 upsert를 호출하고 파일을 삭제합니다."""

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            incoming = root / "incoming"
            incoming.mkdir()
            source = incoming / "65635_CT_PROCESS_COMMENT_20260529_1300.csv.deflate"
            _write_deflate_csv(source, [_build_comment_row()])

            summary = loader_module.load_ct_process_comment_files(data_dir=root)

            self.assertEqual(summary.success_count, 1)
            self.assertFalse(source.exists())
            self.assertEqual(list((root / "processing").iterdir()), [])

        upsert_rows.assert_called_once()
        self.assertEqual(CtProcessCommentLoadJob.objects.filter(status="success").count(), 1)

    @patch.object(loader_module, "_upsert_rows", side_effect=ValueError("copy failed"))
    def test_loader_deletes_file_even_when_upsert_fails(self, upsert_rows) -> None:
        """DB 반영 실패 시에도 처리 파일을 삭제하고 실패 이력을 남깁니다."""

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            incoming = root / "incoming"
            incoming.mkdir()
            source = incoming / "65635_CT_PROCESS_COMMENT_20260529_1300.csv.deflate"
            _write_deflate_csv(source, [_build_comment_row()])

            summary = loader_module.load_ct_process_comment_files(data_dir=root)

            self.assertEqual(summary.failure_count, 1)
            self.assertFalse(source.exists())
            self.assertEqual(list((root / "processing").iterdir()), [])

        upsert_rows.assert_called_once()
        self.assertEqual(CtProcessCommentLoadJob.objects.filter(status="failed").count(), 1)
