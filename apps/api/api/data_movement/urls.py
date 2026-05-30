"""data_movement API 라우팅입니다."""

from __future__ import annotations

from django.urls import path

from api.data_movement.views import DataMovementLoadTriggerView

urlpatterns = [
    path("<str:table_name>/load/", DataMovementLoadTriggerView.as_view(), name="data-movement-load"),
]
