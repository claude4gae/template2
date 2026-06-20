"""data_movement Airflow trigger API 테스트입니다."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, TestCase, override_settings

from api.data_movement.common.services.file_loader import list_data_files
from api.data_movement.m_tkin_prevent.models import MTkinPreventLoadJob
from api.data_movement.m_tkin_prevent.services.loader import LoadFileOutcome, LoadRunSummary


class DataMovementFileLoaderTests(SimpleTestCase):
    """data movement 공통 파일 탐색 동작을 검증합니다."""

    def test_list_data_files_matches_file_name_case_insensitively(self) -> None:
        """파일명 대소문자가 달라도 spec pattern에 맞는 파일을 찾습니다."""

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            matched = root / "65635_ct_process_comment_20260529_1300.CSV.DEFLATE"
            ignored = root / "other.txt"
            matched.write_text("ok", encoding="utf-8")
            ignored.write_text("skip", encoding="utf-8")

            files = list_data_files(
                data_dir=root,
                pattern="*_CT_PROCESS_COMMENT_*.csv.deflate",
            )

        self.assertEqual([path.name for path in files], [matched.name])


@override_settings(AIRFLOW_TRIGGER_TOKEN="test-token")
class DataMovementLoadTriggerApiTests(TestCase):
    """data_movement loader trigger API 동작을 검증합니다."""

    def test_load_trigger_requires_airflow_bearer_token(self) -> None:
        """Bearer token이 없으면 적재를 실행하지 않습니다."""

        response = self.client.post("/api/v1/data-movement/m_tkin_prevent/load/")

        self.assertEqual(response.status_code, 401)

    def test_load_trigger_runs_table_loader(self) -> None:
        """지원 테이블 요청이면 loader를 실행하고 summary를 반환합니다."""

        summary = LoadRunSummary(
            outcomes=[
                LoadFileOutcome(
                    file_name="a.csv.deflate",
                    status=MTkinPreventLoadJob.Status.SUCCESS,
                    row_count=1,
                    replace_values=["L1"],
                )
            ]
        )
        load_files = Mock(return_value=summary)
        with patch.dict("api.data_movement.views.DATA_MOVEMENT_LOADERS", {"m_tkin_prevent": load_files}):
            response = self.client.post(
                "/api/v1/data-movement/m_tkin_prevent/load/",
                data={"limit": 1, "dry_run": True},
                content_type="application/json",
                HTTP_AUTHORIZATION="Bearer test-token",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success_count"], 1)
        load_files.assert_called_once_with(dry_run=True, limit=1)

    def test_load_trigger_rejects_unknown_table(self) -> None:
        """지원하지 않는 테이블명은 404로 거절합니다."""

        response = self.client.post(
            "/api/v1/data-movement/unknown_table/load/",
            HTTP_AUTHORIZATION="Bearer test-token",
        )

        self.assertEqual(response.status_code, 404)
