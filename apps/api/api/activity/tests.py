# =============================================================================
# 모듈 설명: activity 엔드포인트 테스트를 제공합니다.
# - 주요 대상: ActivityLogView(인증/권한/응답 검증)
# - 불변 조건: URL 네임(activity-logs)이 등록되어 있어야 합니다.
# =============================================================================
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from django.urls import reverse

from api.activity.models import ActivityLog


class ActivityLogEndpointTests(TestCase):
    """Activity 로그 조회 엔드포인트 테스트 모음."""

    def setUp(self) -> None:
        """테스트에 사용할 기본 사용자 계정을 생성합니다."""
        # -----------------------------------------------------------------------------
        # 1) 기본 사용자 생성
        # -----------------------------------------------------------------------------
        User = get_user_model()
        self.user = User.objects.create_user(
            sabun="S70000",
            password="test-password",
            knox_id="knox-70000",
        )

    def test_activity_logs_requires_auth(self) -> None:
        """미인증 요청은 401을 반환하는지 확인합니다."""
        response = self.client.get(reverse("activity-logs"))
        self.assertEqual(response.status_code, 401)

    def test_activity_logs_requires_permission(self) -> None:
        """권한이 없을 때 403을 반환하는지 확인합니다."""
        # -----------------------------------------------------------------------------
        # 1) 로그인 후 접근 시도
        # -----------------------------------------------------------------------------
        self.client.force_login(self.user)

        response = self.client.get(reverse("activity-logs"))
        self.assertEqual(response.status_code, 403)

    def test_activity_logs_returns_recent_entries(self) -> None:
        """정상 요청 시 최근 로그 목록이 반환되는지 확인합니다."""
        # -----------------------------------------------------------------------------
        # 1) ActivityLog 생성
        # -----------------------------------------------------------------------------
        ActivityLog.objects.create(
            user=self.user,
            action="UPDATE",
            path="/api/v1/demo",
            method="PATCH",
            status_code=200,
            metadata={"note": "ok"},
        )

        # -----------------------------------------------------------------------------
        # 2) 권한 부여 및 요청 수행
        # -----------------------------------------------------------------------------
        permission = Permission.objects.get(
            content_type__app_label="activity",
            codename="view_activitylog",
        )
        self.user.user_permissions.add(permission)
        self.client.force_login(self.user)

        # -----------------------------------------------------------------------------
        # 3) 응답 검증
        # -----------------------------------------------------------------------------
        response = self.client.get(reverse("activity-logs"), {"limit": "5"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["results"]), 1)
        self.assertEqual(payload["results"][0]["action"], "UPDATE")

    def test_activity_logs_handles_missing_profile(self) -> None:
        """프로필이 없는 사용자도 오류 없이 응답되는지 확인합니다."""
        # -----------------------------------------------------------------------------
        # 1) 프로필 제거(있다면)
        # -----------------------------------------------------------------------------
        try:
            self.user.profile.delete()
        except ObjectDoesNotExist:
            pass
        self.user.refresh_from_db()

        # -----------------------------------------------------------------------------
        # 2) ActivityLog 생성
        # -----------------------------------------------------------------------------
        ActivityLog.objects.create(
            user=self.user,
            action="VIEW",
            path="/api/v1/activity/logs",
            method="GET",
            status_code=200,
            metadata={"note": "ok"},
        )

        # -----------------------------------------------------------------------------
        # 3) 권한 부여 및 요청 수행
        # -----------------------------------------------------------------------------
        permission = Permission.objects.get(
            content_type__app_label="activity",
            codename="view_activitylog",
        )
        self.user.user_permissions.add(permission)
        self.client.force_login(self.user)

        response = self.client.get(reverse("activity-logs"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["results"]), 1)
        self.assertIsNone(payload["results"][0]["role"])
