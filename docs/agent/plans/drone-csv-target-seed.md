# ExecPlan: Drone CSV Target Seed

## 목표
- `seed_drone_targets_from_file --file`이 기존 JSON 파일과 CSV 파일을 모두 읽도록 한다.
- 하나의 target에 여러 mapping이 있는 경우 CSV에서 같은 target을 여러 행으로 표현할 수 있게 한다.
- CSV 예시 파일과 회귀 테스트를 추가한다.

## 현재 상태
- `apps/api/api/drone/management/commands/seed_drone_targets_from_file.py`는 JSON만 `json.load()`로 읽는다.
- `services.seed_drone_sop_notification_defaults_from_rows`는 row 하나 안의 `mappings` list를 처리한다.
- 기존 예시는 `docs/examples/drone_targets.sample.json`이며, CSV 샘플은 단일 mapping 행만 있다.

## 범위
- 수정: Drone seed management command, Drone 테스트, docs/examples CSV 예시, 관련 command README/운영 문서.
- 제외: DB schema/migration, API endpoint, 프론트엔드, seed service public facade 변경.

## 설계
- 파일 확장자가 `.csv`이면 `csv.DictReader`로 읽고, 그 외는 기존 JSON 로직을 유지한다.
- CSV는 mapping마다 한 행을 사용한다. 동일 `target_user_sdwt_prod` 행은 target/channel/rule 설정이 동일해야 한다.
- CSV loader가 동일 target 행들을 하나의 dict로 묶고 `mappings` list를 누적해 기존 service 입력 구조로 변환한다.
- migration/env/auth 영향은 없다.

## 실행 단계
- [x] CSV loader와 값 정규화 함수를 command에 추가한다.
- [x] 동일 target 다중 mapping CSV 테스트와 dry-run 테스트를 추가한다.
- [x] 다중 mapping CSV 예시 파일을 추가하고 기존 CSV 샘플을 필요 시 보강한다.
- [x] README/운영 문서의 JSON 전용 설명을 JSON/CSV로 갱신한다.

## 검증
- 실행 명령: `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.drone.tests.DroneSopJsonTargetSeedTests`
- 기대 결과: 기존 JSON 테스트와 신규 CSV 테스트가 통과한다.

## 위험과 대응
- 위험: 같은 target의 CSV 행이 서로 다른 채널 설정을 갖는 경우 조용히 덮어쓸 수 있다.
- 대응: mapping 외 target/channel/rule 컬럼 불일치는 `CommandError`로 중단한다.
- 위험: CSV boolean/int 값이 모호하면 잘못된 seed가 생성될 수 있다.
- 대응: 빈 값은 기본값 위임, 잘못된 boolean/int 값은 명시 오류로 처리한다.

## 진행 기록
- 2026-05-22: CSV 파일 지원과 다중 mapping 행 표현 방식으로 구현 방향을 확정했다.
- 2026-05-22: CSV loader, 다중 mapping 예시, command 테스트, 관련 운영 문서를 추가했다.
- 2026-05-22: `api.drone.tests.DroneSopJsonTargetSeedTests --keepdb`가 통과했다.
