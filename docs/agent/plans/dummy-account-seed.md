# ExecPlan: dummy account seed

## 목표
- 로컬 개발 환경에서 더미 ADFS 사용자가 별도 소속 설정 없이 로그인 후 앱을 사용할 수 있게 한다.

## 현재 상태
- 더미 ADFS 기본 사용자는 `S000001` / `dummy.user` / `dummy.user@example.com`이다.
- 앱 소속은 `account` 도메인의 `Affiliation`, `UserCurrentAffiliation` 모델로 관리된다.
- `api` 컨테이너 시작 시 `migrate`, `seed_dummy_emails`, `runserver`만 실행한다.

## 범위
- `account` 도메인에 dev seed management command를 추가한다.
- `compose/dev.app.yml`의 `api` entrypoint에서 seed command를 실행한다.
- 더미 ADFS에 dev 전용 자동 sign-in 옵션을 추가한다.
- command 동작을 검증하는 backend 테스트를 추가한다.
- 운영 auth contract, DB schema, migration은 변경하지 않는다.

## 설계
- command는 환경변수 또는 옵션으로 더미 사용자와 소속 값을 받는다.
- 기본값은 더미 ADFS 기본값과 맞춘다.
- `set_current_affiliation_for_user` 서비스를 사용해 소속 옵션과 현재 소속을 생성/갱신한다.
- `DUMMY_ADFS_AUTO_SIGN_IN=1`이면 더미 ADFS GET `/authorize`가 기본 claims로 form_post callback을 자동 제출한다.
- 스키마 변경이 없으므로 migration은 없다.

## 실행 단계
- [x] account management command 추가
- [x] dev compose entrypoint에 seed 실행 추가
- [x] 더미 ADFS 자동 sign-in 옵션 추가
- [x] command 테스트 추가
- [x] Docker Compose `api` 컨테이너에서 관련 테스트 실행
- [x] dev 컨테이너에서 command와 auth 응답 확인

## 검증
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.account.tests.SeedDummyAccountCommandTests`
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py seed_dummy_account`
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py shell -c "..."`
- `docker compose -f docker-compose.dev.yml up -d --build adfs`
- `curl -s "http://localhost:9102/authorize?..."`

## 위험과 대응
- 위험: 더미 전용 seed가 운영에서 실행될 수 있다.
- 대응: dev compose entrypoint에서만 호출하고 command는 기본값을 local dummy identity로 제한한다.

## 진행 기록
- 2026-06-11: 더미 사용자 소속 선생성 요구와 기존 account 소속 모델/서비스를 확인했다.
- 2026-06-11: `seed_dummy_account` command와 dev entrypoint 실행, command 테스트를 추가했다.
- 2026-06-11: 관련 테스트, `manage.py check`, 실제 dev DB seed, `auth/me` payload 확인을 완료했다.
- 2026-06-11: 더미 ADFS `DUMMY_ADFS_AUTO_SIGN_IN` 옵션과 dev compose wiring을 추가했다.
- 2026-06-11: ADFS 이미지를 재빌드하고 컨테이너 내부 `/authorize` 자동 callback form 응답을 확인했다.
