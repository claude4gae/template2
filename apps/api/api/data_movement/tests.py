"""data_movement Airflow trigger API 테스트입니다."""

from __future__ import annotations

from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from api.data_movement.m_tkin_prevent.models import MTkinPreventLoadJob
from api.data_movement.m_tkin_prevent.services.loader import LoadFileOutcome, LoadRunSummary


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
