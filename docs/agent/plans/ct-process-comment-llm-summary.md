# ExecPlan: ct_process_comment LLM summary column

## 목표
- `ct_process_comment`에 `contents_text`의 LLM 요약 결과를 저장할 수 있는 `llm_summary` 컬럼을 추가한다.

## 현재 상태
- `CtProcessComment`는 원천 파일 컬럼과 적재 상태용 `update_flag`를 저장한다.
- 원천 CSV에는 LLM 요약 컬럼이 없고, 요약 생성/외부 LLM 호출 서비스는 아직 없다.

## 범위
- 수정: `ct_process_comment` model, migration, loader, tests.
- 제외: 실제 LLM 호출, 요약 생성 batch/API, update flag 처리 완료 service.

## 설계
- `CtProcessComment.llm_summary`를 nullable `TextField`로 추가한다.
- 신규 적재 row는 `llm_summary=NULL`로 시작한다.
- 기존 row upsert 시 `contents_text`가 바뀌면 기존 요약이 stale해지므로 `llm_summary=NULL`로 비운다.
- `contents_text`가 동일하고 다른 컬럼만 바뀌면 기존 `llm_summary`를 보존한다.
- 원천 CSV 선별 컬럼(`spec.DB_COLUMNS`)에는 `llm_summary`를 넣지 않는다.

## 실행 단계
- [x] 모델에 `llm_summary` 추가
- [x] loader upsert SQL에서 `contents_text` 변경 시 summary 초기화
- [x] 테스트 보강
- [x] migration 생성 및 검토

## 검증
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py makemigrations ct_process_comment`
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.data_movement.ct_process_comment --keepdb`
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py makemigrations --check --dry-run`
- `npm run agent:audit:api-boundary`

## 위험과 대응
- 위험: `contents_text` 변경 후 기존 요약이 남아 잘못 재사용될 수 있다.
- 대응: upsert에서 `contents_text` 변경 시 `llm_summary`를 `NULL`로 초기화한다.

## 진행 기록
- 2026-06-19: 사용자 요청에 따라 `llm_summary` 저장 컬럼 추가를 시작했다.
- 2026-06-19: `ct_process_comment` 앱 테스트 11건, migration check, backend boundary audit을 통과했다.
