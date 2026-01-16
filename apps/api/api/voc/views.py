# =============================================================================
# 모듈 설명: voc 게시판 CRUD APIView를 제공합니다.
# - 주요 클래스: VocPostsView, VocPostDetailView, VocReplyView
# - 불변 조건: 상태 값은 STATUS_SET 기준이며 JSON 바디를 사용합니다.
# =============================================================================

"""VOC(Q&A) 게시판 CRUD 뷰.

- GET    /api/v1/voc/posts                          : 게시글 목록 조회
- POST   /api/v1/voc/posts                          : 새 게시글 생성
- PATCH  /api/v1/voc/posts/<id>                     : 제목/내용/상태 수정
- DELETE /api/v1/voc/posts/<id>                     : 게시글 삭제(작성자+관리자)
- POST   /api/v1/voc/posts/<id>/replies             : 답변 추가
"""
from __future__ import annotations

import logging

from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView

from api.common.services import (
    merge_activity_metadata,
    set_activity_new_state,
    set_activity_previous_state,
    set_activity_summary,
)
from api.common.services import parse_json_body

from .selectors import (
    get_default_post_app,
    get_default_post_status,
    get_post_detail,
    get_post_list,
    get_status_counts,
    get_valid_post_apps,
    get_valid_post_statuses,
)
from .serializers import serialize_post, serialize_reply
from .services import add_reply, can_manage_post, create_post, delete_post, update_post

logger = logging.getLogger(__name__)

# =============================================================================
# 상수: 상태/앱 집합 및 제목/앱 길이 제한
# =============================================================================
STATUS_SET = get_valid_post_statuses()
APP_SET = get_valid_post_apps()
MAX_TITLE_LENGTH = 255
MAX_APP_LENGTH = 80


@method_decorator(csrf_exempt, name="dispatch")
class VocPostsView(APIView):
    """목록 조회 및 신규 작성."""

    def get(self, request: HttpRequest, *args: object, **kwargs: object) -> JsonResponse:
        """게시글 목록을 조회합니다.

        입력:
        - 요청: Django HttpRequest
        - args/kwargs: URL 라우팅 인자

        반환:
        - JsonResponse: 게시글 목록 및 statusCounts

        부작용:
        - 없음(읽기 전용)

        오류:
        - 400: status 값이 유효하지 않을 때

        예시 요청:
        - 예시 요청: GET /api/v1/voc/posts
        - 예시 요청: GET /api/v1/voc/posts?status=접수

        snake/camel 호환:
        - status 키 동일
        """
        # -----------------------------------------------------------------------------
        # 1) 상태 필터 검증
        # -----------------------------------------------------------------------------
        status_filter = request.GET.get("status")
        if status_filter:
            if status_filter not in STATUS_SET:
                return JsonResponse({"error": "Invalid status value"}, status=400)

        # -----------------------------------------------------------------------------
        # 2) 게시글 목록 조회/직렬화
        # -----------------------------------------------------------------------------
        queryset = get_post_list(status=status_filter)
        posts = [serialize_post(post) for post in queryset]

        # -----------------------------------------------------------------------------
        # 3) 응답 반환
        # -----------------------------------------------------------------------------
        return JsonResponse(
            {
                "results": posts,
                "total": len(posts),
                "statusCounts": get_status_counts(),
            }
        )

    def post(self, request: HttpRequest, *args: object, **kwargs: object) -> JsonResponse:
        """게시글을 생성합니다.

        입력:
        - 요청: Django HttpRequest(JSON 바디: title, content, status, app)
        - args/kwargs: URL 라우팅 인자

        반환:
        - JsonResponse: 생성된 게시글 및 statusCounts

        부작용:
        - VocPost 레코드 생성
        - 활동 로그 기록(activity_logging)

        오류:
        - 401: 인증 필요
        - 400: JSON 파싱 실패/필수 필드 누락/상태 값 오류/제목·앱 길이 초과/앱 값 오류
        - 500: 생성 실패

        예시 요청:
        - 예시 요청: POST /api/v1/voc/posts
          예시 바디: {"title":"제목","content":"내용","status":"접수","app":"기타"}

        snake/camel 호환:
        - title/content/status/app 키 동일
        """
        # -----------------------------------------------------------------------------
        # 1) 인증 확인
        # -----------------------------------------------------------------------------
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)

        # -----------------------------------------------------------------------------
        # 2) 요청 바디 파싱
        # -----------------------------------------------------------------------------
        payload = parse_json_body(request)
        if payload is None:
            return JsonResponse({"error": "Invalid JSON body"}, status=400)

        # -----------------------------------------------------------------------------
        # 3) 입력 정규화 및 검증
        # -----------------------------------------------------------------------------
        title = str(payload.get("title") or "").strip()
        content = str(payload.get("content") or "").strip()
        status = payload.get("status") or get_default_post_status()
        app = str(payload.get("app") or "").strip()

        if not title:
            return JsonResponse({"error": "title is required"}, status=400)
        if len(title) > MAX_TITLE_LENGTH:
            return JsonResponse({"error": "title is too long"}, status=400)
        if not content:
            return JsonResponse({"error": "content is required"}, status=400)
        if status not in STATUS_SET:
            return JsonResponse({"error": "Invalid status value"}, status=400)
        if not app:
            return JsonResponse({"error": "app is required"}, status=400)
        if len(app) > MAX_APP_LENGTH:
            return JsonResponse({"error": "app is too long"}, status=400)
        if app not in APP_SET:
            return JsonResponse({"error": "Invalid app value"}, status=400)

        # -----------------------------------------------------------------------------
        # 4) 생성 및 활동 로그 기록
        # -----------------------------------------------------------------------------
        try:
            post = create_post(
                title=title,
                content=content,
                status=status,
                app=app or get_default_post_app(),
                author=request.user,
            )

            set_activity_summary(request, "Create VOC post")
            set_activity_new_state(request, serialize_post(post))
            merge_activity_metadata(request, resource="voc_post", entryId=post.pk)

            return JsonResponse(
                {"post": serialize_post(post), "statusCounts": get_status_counts()}, status=201
            )
        except Exception:  # 방어적 로깅: pragma: no cover
            logger.exception("Failed to create VOC post")
            return JsonResponse({"error": "Failed to create post"}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class VocPostDetailView(APIView):
    """단일 게시글 수정/삭제."""

    def patch(self, request: HttpRequest, post_id: int, *args: object, **kwargs: object) -> JsonResponse:
        """게시글을 수정합니다.

        입력:
        - 요청: Django HttpRequest(JSON 바디: title/content/status/app 선택)
        - post_id: 게시글 ID
        - args/kwargs: URL 라우팅 인자

        반환:
        - JsonResponse: 수정된 게시글 및 statusCounts

        부작용:
        - VocPost 레코드 갱신
        - 활동 로그 기록(activity_logging)

        오류:
        - 401: 인증 필요
        - 400: JSON 파싱 실패/입력 오류/앱 값 오류/변경 없음
        - 403: 권한 없음
        - 404: 게시글 없음
        - 500: 수정 실패

        예시 요청:
        - 예시 요청: PATCH /api/v1/voc/posts/1
          예시 바디: {"title":"수정","status":"진행중","app":"기타"}

        snake/camel 호환:
        - title/content/status/app 키 동일
        """
        # -----------------------------------------------------------------------------
        # 1) 인증 확인
        # -----------------------------------------------------------------------------
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)

        # -----------------------------------------------------------------------------
        # 2) 요청 바디 파싱
        # -----------------------------------------------------------------------------
        payload = parse_json_body(request)
        if payload is None:
            return JsonResponse({"error": "Invalid JSON body"}, status=400)

        # -----------------------------------------------------------------------------
        # 3) 게시글 조회
        # -----------------------------------------------------------------------------
        try:
            post = get_post_detail(post_id=post_id)
        except Exception:
            post = None
        if not post:
            return JsonResponse({"error": "Post not found"}, status=404)

        # -----------------------------------------------------------------------------
        # 4) 권한 확인
        # -----------------------------------------------------------------------------
        if not can_manage_post(user=request.user, post=post):
            return JsonResponse({"error": "Forbidden"}, status=403)

        # -----------------------------------------------------------------------------
        # 5) 업데이트 데이터 구성/검증
        # -----------------------------------------------------------------------------
        updates = {}
        if "title" in payload:
            title = str(payload.get("title") or "").strip()
            if not title:
                return JsonResponse({"error": "title is required"}, status=400)
            if len(title) > MAX_TITLE_LENGTH:
                return JsonResponse({"error": "title is too long"}, status=400)
            updates["title"] = title

        if "content" in payload:
            content = str(payload.get("content") or "").strip()
            if not content:
                return JsonResponse({"error": "content is required"}, status=400)
            updates["content"] = content

        if "status" in payload:
            status = payload.get("status")
            if status not in STATUS_SET:
                return JsonResponse({"error": "Invalid status value"}, status=400)
            updates["status"] = status

        if "app" in payload:
            app = str(payload.get("app") or "").strip()
            if not app:
                return JsonResponse({"error": "app is required"}, status=400)
            if len(app) > MAX_APP_LENGTH:
                return JsonResponse({"error": "app is too long"}, status=400)
            if app not in APP_SET:
                return JsonResponse({"error": "Invalid app value"}, status=400)
            updates["app"] = app

        if not updates:
            return JsonResponse({"error": "No changes provided"}, status=400)

        # -----------------------------------------------------------------------------
        # 6) 업데이트 수행 및 활동 로그 기록
        # -----------------------------------------------------------------------------
        try:
            before = serialize_post(post)
            post = update_post(post=post, updates=updates)

            set_activity_summary(request, "Update VOC post")
            set_activity_previous_state(request, before)
            set_activity_new_state(request, serialize_post(post))
            merge_activity_metadata(request, resource="voc_post", entryId=post.pk)

            return JsonResponse({"post": serialize_post(post), "statusCounts": get_status_counts()})
        except Exception:  # 방어적 로깅: pragma: no cover
            logger.exception("Failed to update VOC post")
            return JsonResponse({"error": "Failed to update post"}, status=500)

    def delete(self, request: HttpRequest, post_id: int, *args: object, **kwargs: object) -> JsonResponse:
        """게시글을 삭제합니다.

        입력:
        - 요청: Django HttpRequest
        - post_id: 게시글 ID
        - args/kwargs: URL 라우팅 인자

        반환:
        - JsonResponse: 삭제 성공 여부 및 statusCounts

        부작용:
        - VocPost 레코드 삭제
        - 활동 로그 기록(activity_logging)

        오류:
        - 401: 인증 필요
        - 403: 권한 없음
        - 404: 게시글 없음
        - 500: 삭제 실패

        예시 요청:
        - 예시 요청: DELETE /api/v1/voc/posts/1

        snake/camel 호환:
        - 해당 없음(요청 바디 없음)
        """
        # -----------------------------------------------------------------------------
        # 1) 인증 확인
        # -----------------------------------------------------------------------------
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)

        # -----------------------------------------------------------------------------
        # 2) 게시글 조회
        # -----------------------------------------------------------------------------
        try:
            post = get_post_detail(post_id=post_id)
        except Exception:
            post = None
        if not post:
            return JsonResponse({"error": "Post not found"}, status=404)

        # -----------------------------------------------------------------------------
        # 3) 권한 확인
        # -----------------------------------------------------------------------------
        if not can_manage_post(user=request.user, post=post):
            return JsonResponse({"error": "Forbidden"}, status=403)

        # -----------------------------------------------------------------------------
        # 4) 삭제 수행 및 활동 로그 기록
        # -----------------------------------------------------------------------------
        try:
            before = serialize_post(post)
            delete_post(post=post)

            set_activity_summary(request, "Delete VOC post")
            set_activity_previous_state(request, before)
            merge_activity_metadata(request, resource="voc_post", entryId=post_id)

            return JsonResponse({"success": True, "statusCounts": get_status_counts()})
        except Exception:  # 방어적 로깅: pragma: no cover
            logger.exception("Failed to delete VOC post")
            return JsonResponse({"error": "Failed to delete post"}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class VocReplyView(APIView):
    """답변 추가."""

    def post(self, request: HttpRequest, post_id: int, *args: object, **kwargs: object) -> JsonResponse:
        """게시글에 답변을 추가합니다.

        입력:
        - 요청: Django HttpRequest(JSON 바디: content)
        - post_id: 게시글 ID
        - args/kwargs: URL 라우팅 인자

        반환:
        - JsonResponse: 생성된 답변 및 갱신된 게시글

        부작용:
        - VocReply 레코드 생성
        - 활동 로그 기록(activity_logging)

        오류:
        - 401: 인증 필요
        - 400: JSON 파싱 실패/내용 누락
        - 404: 게시글 없음
        - 500: 답변 추가 실패

        예시 요청:
        - 예시 요청: POST /api/v1/voc/posts/1/replies
          예시 바디: {"content":"답변 내용"}

        snake/camel 호환:
        - content 키 동일
        """
        # -----------------------------------------------------------------------------
        # 1) 인증 확인
        # -----------------------------------------------------------------------------
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)

        # -----------------------------------------------------------------------------
        # 2) 요청 바디 파싱
        # -----------------------------------------------------------------------------
        payload = parse_json_body(request)
        if payload is None:
            return JsonResponse({"error": "Invalid JSON body"}, status=400)

        # -----------------------------------------------------------------------------
        # 3) 내용 검증
        # -----------------------------------------------------------------------------
        content = str(payload.get("content") or "").strip()
        if not content:
            return JsonResponse({"error": "content is required"}, status=400)

        # -----------------------------------------------------------------------------
        # 4) 게시글 조회
        # -----------------------------------------------------------------------------
        post = get_post_detail(post_id=post_id)
        if not post:
            return JsonResponse({"error": "Post not found"}, status=404)

        # -----------------------------------------------------------------------------
        # 5) 답변 추가 및 활동 로그 기록
        # -----------------------------------------------------------------------------
        try:
            reply, refreshed_post = add_reply(post=post, author=request.user, content=content)

            set_activity_summary(request, "Add VOC reply")
            set_activity_new_state(request, serialize_reply(reply))
            merge_activity_metadata(request, resource="voc_reply", entryId=reply.pk, postId=post_id)

            return JsonResponse(
                {"reply": serialize_reply(reply), "post": serialize_post(refreshed_post)}, status=201
            )
        except Exception:  # 방어적 로깅: pragma: no cover
            logger.exception("Failed to add VOC reply")
            return JsonResponse({"error": "Failed to add reply"}, status=500)


__all__ = ["VocPostsView", "VocPostDetailView", "VocReplyView"]
