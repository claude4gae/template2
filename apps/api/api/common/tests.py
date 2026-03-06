# =============================================================================
# 모듈 설명: common 서비스 유틸 테스트를 제공합니다.
# - 주요 대상: normalize_text
# - 불변 조건: DB 접근 없이 순수 함수 동작만 검증합니다.
# =============================================================================

from __future__ import annotations

from django.test import SimpleTestCase

from api.common.services import normalize_text


class CommonNormalizationTests(SimpleTestCase):
    """공용 정규화 유틸 동작을 검증합니다."""

    def test_normalize_text_trims_text(self) -> None:
        """문자열 입력의 앞뒤 공백이 제거되는지 확인합니다."""

        self.assertEqual(normalize_text("  hello  "), "hello")

    def test_normalize_text_returns_empty_for_non_string(self) -> None:
        """문자열이 아니면 빈 문자열을 반환하는지 확인합니다."""

        self.assertEqual(normalize_text(None), "")
        self.assertEqual(normalize_text(123), "")
