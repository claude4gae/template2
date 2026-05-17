# AppStore 모듈

AppStore는 내부 앱과 도구를 등록하고 공유하는 기능입니다.

## 기능 요약

- 앱 목록/상세 조회
- 앱 등록/수정/삭제
- 대표 이미지 제공
- 앱 좋아요/조회수
- 댓글/대댓글
- 댓글 좋아요

## 권한

- 앱 등록, 좋아요, 댓글 작성은 로그인 사용자가 수행합니다.
- 앱 수정/삭제는 작성자 또는 관리자만 가능합니다.
- 댓글 수정/삭제는 작성자 또는 관리자만 가능합니다.

## 앱 등록 흐름

1. 사용자가 앱 이름, URL, 설명, 카테고리, 스크린샷을 제출합니다.
2. 서버가 필수값과 길이를 검증합니다.
3. 스크린샷을 대표 이미지와 gallery로 정리합니다.
4. 앱을 저장하고 payload를 반환합니다.

## 대표 이미지

대표 이미지가 URL이면 redirect하고, base64/data URL이면 이미지 바이너리로 응답합니다.

## 화면/API/데이터 추적

| 구간 | 위치 |
| --- | --- |
| 화면 | `/appstore` |
| Frontend | `apps/web/src/features/appstore` |
| Backend API | `/api/v1/appstore/**` |
| 데이터 | `AppStoreApp`, `AppStoreLike`, `AppStoreComment`, `AppStoreCommentLike` |
| 파일/이미지 | cover endpoint가 URL redirect 또는 이미지 바이너리를 반환 |

## 운영 포인트

- 이미지가 깨지면 cover URL/data URL 형식과 `/cover` 응답 방식을 확인합니다.
- 수정/삭제 403은 작성자와 관리자 권한을 확인합니다.
- 댓글/좋아요 불일치는 앱/댓글 ID와 로그인 사용자 기준 중복 여부를 확인합니다.

## 관련 API

- `docs/api/appstore.md`

## 관련 코드

- `apps/api/api/appstore/views.py`
- `apps/api/api/appstore/models.py`
- `apps/api/api/appstore/selectors.py`
- `apps/api/api/appstore/serializers.py`
- `apps/api/api/appstore/services/apps.py`
- `apps/api/api/appstore/services/comments.py`
- `apps/api/api/appstore/services/likes.py`
- `apps/api/api/appstore/services/screenshots.py`
- `apps/web/src/features/appstore`
