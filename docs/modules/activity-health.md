# Activity / Health 모듈

Activity는 변경 작업 로그 조회, Health는 서버 상태 확인을 담당합니다.

## Activity 기능

- 최근 ActivityLog 조회
- 조회 권한 검사
- 로그 직렬화

ActivityLog 생성은 `api.common`의 middleware가 수행합니다.

## Activity 권한

다음 중 하나가 필요합니다.

- `activity.view_activitylog`
- `api.view_activitylog`

## Health 기능

Health는 인증 없이 서버 상태를 반환합니다.

```json
{
  "status": "ok",
  "application": "template2-api"
}
```

## API/데이터 추적

| 구간 | 위치 |
| --- | --- |
| Activity API | `/api/v1/activity/logs` |
| Health API | `/api/v1/health/` |
| Backend | `apps/api/api/activity`, `apps/api/api/health` |
| 데이터 | `ActivityLog`, runtime health payload |
| 생성 경로 | `api.common` middleware와 service helper |

## 운영 포인트

- Activity 403은 `activity.view_activitylog` 또는 `api.view_activitylog` 권한을 확인합니다.
- Health 실패는 Django process, DB 연결 여부, reverse proxy routing을 순서대로 확인합니다.
- Activity가 비어 있으면 middleware 적용 여부와 작업별 metadata 주입 여부를 확인합니다.

## 관련 API

- `docs/api/activity-health.md`

## 관련 코드

- `apps/api/api/activity/views.py`
- `apps/api/api/activity/models.py`
- `apps/api/api/activity/selectors.py`
- `apps/api/api/activity/services/activity_logs.py`
- `apps/api/api/health/views.py`
- `apps/api/api/health/services/health_status.py`
- `apps/api/api/common/services/middleware.py`
- `apps/api/api/common/services/activity_logging.py`
