# =============================================================================
# 모듈 설명: AppStore 좋아요/조회수 서비스 로직을 제공합니다.
# - 주요 함수: toggle_like, increment_view_count
# - 불변 조건: like_count/view_count는 원자적으로 갱신합니다.
# =============================================================================
from __future__ import annotations

from typing import Any, Tuple

from django.db import transaction
from django.db.models import F
from django.db.models.functions import Greatest

from ..models import AppStoreApp, AppStoreLike


@transaction.atomic
def toggle_like(*, app: AppStoreApp, user: Any) -> Tuple[bool, int]:
    """앱 좋아요를 토글하고 like_count를 갱신합니다.

    인자:
        app: 대상 앱 인스턴스.
        user: 요청 사용자 인스턴스.

    반환:
        (liked, like_count) 튜플.

    부작용:
        AppStoreLike 생성/삭제 및 like_count 갱신이 발생합니다.

    오류:
        ORM 저장 과정에서 예외가 발생할 수 있습니다.
    """

    # -----------------------------------------------------------------------------
    # 1) 좋아요 토글(행 잠금)
    # -----------------------------------------------------------------------------
    like, created = AppStoreLike.objects.select_for_update().get_or_create(app=app, user=user)
    if created:
        AppStoreApp.objects.filter(pk=app.pk).update(like_count=F("like_count") + 1)
        liked = True
    else:
        like.delete()
        AppStoreApp.objects.filter(pk=app.pk).update(like_count=Greatest(F("like_count") - 1, 0))
        liked = False

    # -----------------------------------------------------------------------------
    # 2) 최신 like_count 재조회
    # -----------------------------------------------------------------------------
    app.refresh_from_db(fields=["like_count"])
    return liked, int(app.like_count or 0)


def increment_view_count(*, app: AppStoreApp) -> int:
    """조회수를 증가시키고 최신 값을 반환합니다.

    인자:
        app: 대상 앱 인스턴스.

    반환:
        갱신된 조회수 값.

    부작용:
        AppStoreApp.view_count를 갱신합니다.

    오류:
        ORM 저장 과정에서 예외가 발생할 수 있습니다.
    """

    # -----------------------------------------------------------------------------
    # 1) 조회수 증가
    # -----------------------------------------------------------------------------
    AppStoreApp.objects.filter(pk=app.pk).update(view_count=F("view_count") + 1)
    # -----------------------------------------------------------------------------
    # 2) 최신 값 재조회
    # -----------------------------------------------------------------------------
    app.refresh_from_db(fields=["view_count"])
    return int(app.view_count or 0)
