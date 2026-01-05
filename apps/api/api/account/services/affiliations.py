# =============================================================================
# 모듈 설명: 소속 관련 서비스 로직을 제공합니다.
# - 주요 대상: get_affiliation_overview, ensure_affiliation_option, submit_affiliation_reconfirm_response
# - 불변 조건: 모든 쓰기 작업은 서비스 레이어에서 수행합니다.
# =============================================================================

"""소속 관련 서비스 로직 모음.

- 주요 대상: 소속 개요, 소속 옵션 보장, 재확인 처리, 옵션 페이로드
- 주요 엔드포인트/클래스: get_affiliation_overview 등
- 가정/불변 조건: 모든 쓰기 작업은 서비스 레이어에서 수행됨
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from django.utils import timezone

from ..models import Affiliation
from .. import selectors
from .access import _current_access_list
from .affiliation_requests import request_affiliation_change


def get_affiliation_overview(*, user: Any, timezone_name: str) -> dict[str, object]:
    """AccountAffiliationView(GET) 응답 payload를 구성합니다.

    입력:
    - user: Django 사용자 객체
    - timezone_name: 시간대 이름

    반환:
    - dict[str, object]: 소속 개요 payload

    부작용:
    - 없음

    오류:
    - 없음
    """

    access_list = _current_access_list(user)
    manageable = [entry["userSdwtProd"] for entry in access_list if entry["canManage"]]
    options = selectors.list_affiliation_options()

    return {
        "currentUserSdwtProd": getattr(user, "user_sdwt_prod", None),
        "currentDepartment": getattr(user, "department", None),
        "currentLine": getattr(user, "line", None),
        "timezone": timezone_name,
        "accessibleUserSdwtProds": access_list,
        "manageableUserSdwtProds": manageable,
        "affiliationOptions": options,
    }


def get_affiliation_reconfirm_status(*, user: Any) -> dict[str, object]:
    """사용자의 소속 재확인 상태와 예측값을 반환합니다.

    입력:
    - user: Django 사용자 객체

    반환:
    - dict[str, object]: 재확인 상태/예측 소속 정보

    부작용:
    - 없음

    오류:
    - 없음
    """

    if not user:
        return {"requiresReconfirm": False, "predictedUserSdwtProd": None, "currentUserSdwtProd": None}

    snapshot = selectors.get_external_affiliation_snapshot_by_knox_id(
        knox_id=getattr(user, "knox_id", "") or ""
    )
    predicted = snapshot.predicted_user_sdwt_prod if snapshot else None
    return {
        "requiresReconfirm": bool(getattr(user, "requires_affiliation_reconfirm", False)),
        "predictedUserSdwtProd": predicted,
        "currentUserSdwtProd": getattr(user, "user_sdwt_prod", None),
    }


def ensure_affiliation_option(
    *,
    department: str,
    line: str,
    user_sdwt_prod: str,
) -> Affiliation:
    """소속 옵션을 생성하거나 기존 행을 갱신합니다.

    입력:
    - department: 부서 식별자
    - line: 라인 식별자
    - user_sdwt_prod: 소속 그룹 값
    반환:
    - Affiliation: 소속 옵션 객체

    부작용:
    - Affiliation 생성

    오류:
    - ValueError: 필수 입력 누락
    """

    # -----------------------------------------------------------------------------
    # 1) 입력 정규화 및 검증
    # -----------------------------------------------------------------------------
    normalized_department = (department or "").strip()
    normalized_line = (line or "").strip()
    normalized_user_sdwt = (user_sdwt_prod or "").strip()
    if not normalized_department or not normalized_line or not normalized_user_sdwt:
        raise ValueError("department/line/user_sdwt_prod is required")

    # -----------------------------------------------------------------------------
    # 2) 옵션 업서트
    # -----------------------------------------------------------------------------
    option, _created = Affiliation.objects.get_or_create(
        department=normalized_department,
        line=normalized_line,
        user_sdwt_prod=normalized_user_sdwt,
    )

    return option


def submit_affiliation_reconfirm_response(
    *,
    user: Any,
    accepted: bool,
    department: str | None,
    line: str | None,
    user_sdwt_prod: str | None,
    timezone_name: str,
) -> Tuple[dict[str, object], int]:
    """재확인 응답을 처리해 소속 변경 요청을 생성합니다.

    입력:
    - user: Django 사용자 객체
    - accepted: 재확인 수락 여부
    - department/line/user_sdwt_prod: 선택된 소속 정보
    - timezone_name: 시간대 이름

    반환:
    - Tuple[dict[str, object], int]: (payload, status_code) (응답 본문, 상태 코드)

    부작용:
    - UserSdwtProdChange 생성
    - 사용자 재확인 플래그 해제 가능

    오류:
    - 400: 입력 오류
    - 401: 미인증
    """

    # -----------------------------------------------------------------------------
    # 1) 사용자 인증 확인
    # -----------------------------------------------------------------------------
    if not user:
        return {"error": "unauthorized"}, 401

    # -----------------------------------------------------------------------------
    # 2) user_sdwt_prod 결정
    # -----------------------------------------------------------------------------
    selected_user_sdwt = (user_sdwt_prod or "").strip()
    if accepted and not selected_user_sdwt:
        snapshot = selectors.get_external_affiliation_snapshot_by_knox_id(
            knox_id=getattr(user, "knox_id", "") or ""
        )
        if snapshot:
            selected_user_sdwt = snapshot.predicted_user_sdwt_prod

    if not selected_user_sdwt:
        return {"error": "user_sdwt_prod is required"}, 400

    # -----------------------------------------------------------------------------
    # 3) 소속 옵션 검증
    # -----------------------------------------------------------------------------
    option = None
    if department and line:
        option = selectors.get_affiliation_option(
            (department or "").strip(),
            (line or "").strip(),
            selected_user_sdwt,
        )
    if option is None:
        option = selectors.get_affiliation_option_by_user_sdwt_prod(
            user_sdwt_prod=selected_user_sdwt
        )
    if option is None:
        return {"error": "Invalid department/line/user_sdwt_prod combination"}, 400

    # -----------------------------------------------------------------------------
    # 4) 변경 요청 생성
    # -----------------------------------------------------------------------------
    response_payload, status_code = request_affiliation_change(
        user=user,
        option=option,
        to_user_sdwt_prod=selected_user_sdwt,
        effective_from=timezone.now(),
        timezone_name=timezone_name,
    )
    # -----------------------------------------------------------------------------
    # 5) 재확인 플래그 해제
    # -----------------------------------------------------------------------------
    if status_code in (200, 202):
        user.requires_affiliation_reconfirm = False
        user.save(update_fields=["requires_affiliation_reconfirm"])

    return response_payload, status_code


def get_line_sdwt_options_payload(*, pairs: list[dict[str, str]]) -> dict[str, object]:
    """(line_id, user_sdwt_prod) 목록으로 LineSdwtOptionsView 응답 payload를 구성합니다.

    입력:
    - pairs: line_id/user_sdwt_prod 쌍 목록

    반환:
    - dict[str, object]: 옵션 페이로드

    부작용:
    - 없음

    오류:
    - 없음
    """

    # -----------------------------------------------------------------------------
    # 1) 라인별 그룹화
    # -----------------------------------------------------------------------------
    grouped: Dict[str, List[str]] = {}
    for row in pairs:
        line_id = row["line_id"]
        user_sdwt_prod = row["user_sdwt_prod"]
        grouped.setdefault(line_id, []).append(user_sdwt_prod)

    # -----------------------------------------------------------------------------
    # 2) 라인별 옵션 구성
    # -----------------------------------------------------------------------------
    lines = [
        {
            "lineId": line_id,
            "userSdwtProds": sorted(list(set(user_sdwt_list))),
        }
        for line_id, user_sdwt_list in grouped.items()
    ]
    # -----------------------------------------------------------------------------
    # 3) 전체 user_sdwt_prod 집합 구성
    # -----------------------------------------------------------------------------
    all_user_sdwt = sorted(
        {usdwt for user_sdwt_list in grouped.values() for usdwt in user_sdwt_list}
    )

    # -----------------------------------------------------------------------------
    # 4) 페이로드 반환
    # -----------------------------------------------------------------------------
    return {"lines": lines, "userSdwtProds": all_user_sdwt}
