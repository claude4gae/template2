# =============================================================================
# 모듈 설명: RAG 서비스 테스트를 제공합니다.
# - 주요 대상: search_rag 요청 페이로드
# - 불변 조건: 외부 호출은 patch로 대체합니다.
# =============================================================================

"""RAG 서비스 테스트 모음.

- 주요 대상: search_rag 요청 페이로드
- 주요 엔드포인트/클래스: RagSearchServiceTests
- 가정/불변 조건: 외부 호출은 patch로 대체함
"""
from __future__ import annotations

from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from api.rag.services import search_rag


class RagSearchServiceTests(SimpleTestCase):
    """RAG 검색 서비스의 요청 페이로드를 검증합니다."""

    def test_search_rag_posts_expected_payload(self) -> None:
        """RAG 검색 요청이 기대 페이로드로 전송되는지 확인합니다."""
        # -------------------------------------------------------------------------
        # 1) 응답 Mock 준비
        # -------------------------------------------------------------------------
        response = Mock()
        response.raise_for_status = Mock()
        response.json.return_value = {"hits": {"hits": []}}

        # -------------------------------------------------------------------------
        # 2) 설정/HTTP 호출 patch 및 실행
        # -------------------------------------------------------------------------
        with patch("api.rag.services.RAG_SEARCH_URL", "http://rag/search"), patch(
            "api.rag.services.RAG_HEADERS", {"Content-Type": "application/json"}
        ), patch("api.rag.services.RAG_PERMISSION_GROUPS", ["group-a"]), patch(
            "api.rag.services.RAG_INDEX_DEFAULT", "rp-idx-default"
        ), patch("api.rag.services.RAG_INDEX_LIST", []), patch(
            "api.rag.services.requests.post", return_value=response
        ) as post:
            result = search_rag("hello", num_result_doc=3, timeout=12)

        # -------------------------------------------------------------------------
        # 3) 응답/요청 페이로드 검증
        # -------------------------------------------------------------------------
        self.assertEqual(result, {"hits": {"hits": []}})

        args, kwargs = post.call_args
        self.assertEqual(args[0], "http://rag/search")
        self.assertEqual(kwargs["headers"], {"Content-Type": "application/json"})
        self.assertEqual(
            kwargs["json"],
            {
                "index_name": "rp-idx-default",
                "permission_groups": ["group-a"],
                "query_text": "hello",
                "num_result_doc": 3,
            },
        )
        self.assertEqual(kwargs["timeout"], 12)

    def test_search_rag_rejects_none_query(self) -> None:
        """query_text가 None이면 ValueError가 발생해야 합니다."""
        # -------------------------------------------------------------------------
        # 1) 설정/HTTP 호출 patch
        # -------------------------------------------------------------------------
        with patch("api.rag.services.RAG_SEARCH_URL", "http://rag/search"), patch(
            "api.rag.services.RAG_HEADERS", {"Content-Type": "application/json"}
        ), patch("api.rag.services.RAG_PERMISSION_GROUPS", ["group-a"]), patch(
            "api.rag.services.RAG_INDEX_DEFAULT", "rp-idx-default"
        ), patch("api.rag.services.RAG_INDEX_LIST", []), patch(
            "api.rag.services.requests.post"
        ) as post:
            # ---------------------------------------------------------------------
            # 2) 실행 및 오류 검증
            # ---------------------------------------------------------------------
            with self.assertRaises(ValueError) as context:
                search_rag(None)

        self.assertIn("query_text is empty", str(context.exception))
        post.assert_not_called()
