# ExecPlan: dashboard DB reset

## 목표
- Django 기본 DB 이름을 `dashboard`로 변경한다.
- 기존 `appdata` DB는 유지하고, 새 `dashboard` DB에 현재 schema를 처음부터 적용한다.
- 운영 신규 시작을 위해 우리 앱 migration history를 초기화하고 새 initial migration으로 시작한다.

## 현재 상태
- DB 이름 기본값은 `env/api.common.env`의 `DJANGO_DB_NAME=appdata`와 `apps/api/config/settings.py` fallback/comment에 남아 있다.
- `docker-compose.dev.yml`에는 PostgreSQL 서비스가 없고, `airflow-postgres` 외부 DB를 참조한다.
- 기존 `appdata` migration 상태는 무시하고 새 DB로 시작해야 한다.
- 운영에서는 실행 중 `makemigrations`를 수행하지 않고, 이미지에 포함된 migration만 적용해야 한다.

## 범위
- 수정: DB 이름 설정, 운영 entrypoint, 우리 앱 migration 파일.
- 수행: `dashboard` DB 재생성 및 `migrate` 검증.
- 제외: Django 기본 앱 migration, 기존 `appdata` 삭제, schema 수동 조작.

## 설계
- `DJANGO_DB_NAME`을 `dashboard`로 변경한다.
- Django 설정 fallback도 `dashboard`로 맞춰 env 누락 시에도 동일한 기본 DB명을 사용한다.
- 우리 앱 migration은 `account`, `activity`, `appstore`, `drone`, `emails`, `voc`의 기존 migration 파일을 제거하고 새 `0001_initial.py`로 재생성한다.
- `api.l3_spider`는 DB 모델이 없으므로 migration 대상에서 제외한다.
- 새 DB 검증을 위해 로컬 `dashboard` DB는 drop/create 후 migrate한다.

## 실행 단계
- [x] DB 이름 설정 변경
- [x] `dashboard` DB 생성 확인
- [x] 새 DB에 `python manage.py migrate --noinput` 실행
- [x] 정합성 검증 및 결과 보고
- [x] 우리 앱 migration history 초기화
- [x] 운영 entrypoint에서 `makemigrations` 제거
- [x] `dashboard` DB 재생성 후 새 initial migration 적용

## 검증
- `git diff --check`
- `docker compose -f docker-compose.dev.yml run --rm --entrypoint python api manage.py makemigrations --check --dry-run`
- `docker compose -f docker-compose.dev.yml run --rm --entrypoint python api manage.py migrate --noinput`
- 필요 시 `showmigrations` 또는 DB 목록 조회

## 위험과 대응
- 위험: 외부 DB 컨테이너/네트워크가 실행 중이 아니면 생성/검증이 실패할 수 있다.
- 대응: 설정 변경은 완료하고, 실패 시 실행해야 할 정확한 명령을 보고한다.
- 위험: `dashboard` DB가 이미 존재하고 일부 migration만 적용된 상태일 수 있다.
- 대응: migration 실패 시 DB 상태를 조회하고 새 DB를 다시 만들지 여부를 사용자에게 확인한다.
- 위험: migration 초기화 후 기존 DB에서 업그레이드 경로가 사라진다.
- 대응: 운영 신규 DB 전용 변경으로 명시하고, 기존 `appdata`는 보존한다.

## 진행 기록
- 2026-05-23: 사용자 답변에 따라 전체 앱 migration 파일은 유지하고, 새 `dashboard` DB 기준으로 처음 적용하는 방향으로 결정.
- 2026-05-23: `dashboard` DB를 생성하고 전체 Django migration을 처음부터 적용했다. `drone.0013_target_fk_delivery_architecture` 포함 전체 migration 적용 성공.
- 2026-05-23: `git diff --check` 통과, `appdata`와 `dashboard` DB 공존 확인, `drone` migration 전체 적용 상태 확인.
- 2026-05-23: 운영 신규 시작 요청에 따라 우리 앱 migration history를 새 initial migration으로 초기화하기로 변경.
- 2026-05-23: 우리 앱 migration을 각 앱 `0001_initial.py`로 재생성하고, 운영 entrypoint에서 `makemigrations`를 제거했다. 로컬 `dashboard` DB를 drop/create 후 새 migration으로 migrate 성공.
- 2026-05-23: `makemigrations --check --dry-run`, `manage.py check`, `git diff --check`, 커스텀 앱 테스트 394개 통과.
