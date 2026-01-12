# =============================================================================
# 모듈 설명: tables 엔드포인트 테스트를 제공합니다.
# - 주요 클래스: TablesEndpointTests
# - 불변 조건: URL 네임(tables, tables-update)이 등록되어 있어야 합니다.
# =============================================================================

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse


class TablesEndpointTests(TestCase):
    def setUp(self) -> None:
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.user = User.objects.create_user(
            sabun="S40000",
            password="test-password",
            knox_id="knox-40000",
        )
        self.client.force_login(self.user)

    @patch("api.tables.services.selectors.fetch_rows")
    @patch("api.tables.services.resolve_table_schema")
    def test_tables_list_returns_payload(self, mock_schema, mock_fetch_rows) -> None:
        mock_schema.return_value = SimpleNamespace(
            name="demo_table",
            columns=["id", "created_at"],
            timestamp_column="created_at",
        )
        mock_fetch_rows.return_value = [{"id": 1, "created_at": "2024-01-01 00:00:00"}]

        response = self.client.get(reverse("tables"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["table"], "demo_table")
        self.assertEqual(payload["rowCount"], 1)

    @patch("api.tables.services.execute")
    @patch("api.tables.services.selectors.fetch_row")
    @patch("api.tables.services.selectors.list_columns")
    def test_tables_update_returns_success(self, mock_columns, mock_fetch_row, mock_execute) -> None:
        mock_columns.return_value = ["id", "comment"]
        mock_execute.return_value = (1, None)
        mock_fetch_row.side_effect = [{"id": 10, "comment": "before"}, {"id": 10, "comment": "updated"}]

        response = self.client.patch(
            reverse("tables-update"),
            data='{"table":"demo_table","id":10,"updates":{"comment":"updated"}}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], True)

    @patch("api.tables.services.execute")
    @patch("api.tables.services.selectors.fetch_row")
    @patch("api.tables.services.selectors.list_columns")
    def test_tables_update_accepts_values_alias(self, mock_columns, mock_fetch_row, mock_execute) -> None:
        mock_columns.return_value = ["id", "comment"]
        mock_execute.return_value = (1, None)
        mock_fetch_row.side_effect = [{"id": 11, "comment": "before"}, {"id": 11, "comment": "updated"}]

        response = self.client.patch(
            reverse("tables-update"),
            data='{"table":"demo_table","id":11,"values":{"comment":"updated"}}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], True)
