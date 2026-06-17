# =============================================================================
# 모듈 설명: activity 엔드포인트 테스트를 제공합니다.
# - 주요 대상: ActivityLogView(인증/권한/응답 검증)
# - 불변 조건: URL 네임(activity-logs)이 등록되어 있어야 합니다.
# =============================================================================
from __future__ import annotations

import json
from datetime import UTC, datetime

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
        self.other_user = User.objects.create_user(
            sabun="S70001",
            password="test-password",
            knox_id="knox-70001",
        )
        self.superuser = User.objects.create_superuser(
            sabun="S70002",
            password="test-password",
            knox_id="knox-70002",
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

    def test_app_access_event_requires_auth(self) -> None:
        """앱 접속 이벤트 기록은 인증을 요구합니다."""
        response = self.client.post(
            reverse("activity-app-access"),
            data=json.dumps({"appId": "appstore", "appName": "Appstore"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_app_access_event_records_activity_log(self) -> None:
        """앱 접속 이벤트 기록 API가 APP_ACCESS 로그를 생성하는지 확인합니다."""
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("activity-app-access"),
            data=json.dumps({"appId": "appstore", "appName": "Appstore", "path": "/appstore"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        entry = ActivityLog.objects.get(pk=response.json()["id"])
        self.assertEqual(entry.action, "APP_ACCESS")
        self.assertEqual(entry.metadata["app_id"], "appstore")
        self.assertEqual(entry.metadata["knox_id"], "knox-70000")

    def test_app_access_stats_requires_superuser(self) -> None:
        """앱 접속 통계 조회는 슈퍼유저만 허용합니다."""
        self.client.force_login(self.user)

        response = self.client.get(reverse("activity-app-access-stats"))

        self.assertEqual(response.status_code, 403)

    def test_app_access_stats_aggregates_by_kst_and_knox_id(self) -> None:
        """KST 날짜 기준과 knox_id distinct 기준으로 앱 접속 통계를 집계합니다."""
        ActivityLog.objects.create(
            user=self.user,
            action="APP_ACCESS",
            path="/appstore",
            method="EVENT",
            status_code=200,
            metadata={"app_id": "appstore", "app_name": "Appstore", "event_type": "app_access"},
            created_at=datetime(2026, 6, 16, 15, 30, tzinfo=UTC),
        )
        ActivityLog.objects.create(
            user=self.user,
            action="APP_ACCESS",
            path="/appstore",
            method="EVENT",
            status_code=200,
            metadata={"app_id": "appstore", "app_name": "Appstore", "event_type": "app_access"},
            created_at=datetime(2026, 6, 17, 1, 0, tzinfo=UTC),
        )
        ActivityLog.objects.create(
            user=self.other_user,
            action="APP_ACCESS",
            path="/emails/inbox",
            method="EVENT",
            status_code=200,
            metadata={"app_id": "emails", "app_name": "Emails", "event_type": "app_access"},
            created_at=datetime(2026, 6, 17, 2, 0, tzinfo=UTC),
        )
        ActivityLog.objects.create(
            user=self.other_user,
            action="GET",
            path="/api/v1/appstore/apps",
            method="GET",
            status_code=200,
            metadata={"app_id": "appstore", "app_name": "Appstore"},
            created_at=datetime(2026, 6, 17, 3, 0, tzinfo=UTC),
        )
        self.client.force_login(self.superuser)

        response = self.client.get(
            reverse("activity-app-access-stats"),
            {"from": "2026-06-17", "to": "2026-06-17"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["timezone"], "Asia/Seoul")
        self.assertEqual(payload["summary"]["totalAccessCount"], 3)
        self.assertEqual(payload["summary"]["uniqueUserCount"], 2)
        self.assertEqual(payload["summary"]["activeAppCount"], 2)
        self.assertEqual(payload["apps"][0]["appId"], "appstore")
        self.assertEqual(payload["apps"][0]["accessCount"], 2)
        self.assertEqual(payload["apps"][0]["uniqueUserCount"], 1)
        self.assertEqual(payload["series"][0]["date"], "2026-06-17")
