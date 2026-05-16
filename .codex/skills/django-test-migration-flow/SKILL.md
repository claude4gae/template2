---
name: django-test-migration-flow
description: |
  Django business logic 변경 시 테스트와 migration을 저장소 규칙에 맞게 추가/검증하고,
  Docker Compose `api` 컨테이너 기준으로 실행하는 스킬.
---

# django-test-migration-flow

## 목적
backend 변경 시 테스트와 migration 누락을 방지하고 container-first 규칙을 지킨다.

## 사용할 때
- service / selector / model / serializer / view 변경 시
- DB schema 변경 시
- business rule 변경 시
- cross-domain 영향이 있는 backend 수정 시

## 핵심 원칙
- business logic이 바뀌면 테스트를 추가/수정한다.
- applied migration은 수정하지 않는다.
- schema 변경은 새 migration으로 처리한다.
- backend 테스트/명령은 Docker Compose `api` 컨테이너에서 실행한다.

## 테스트 우선순위
1. services 테스트
   - 정상 동작, 핵심 business rule, side effect, transaction 경계, 예외 흐름
2. selectors 테스트
   - filtering, ordering, annotation, read model shape
3. views 테스트(최소)
   - happy path, 주요 validation error, permission/auth error

## migration 규칙
- model 변경 시 migration 필요 여부를 먼저 판단한다.
- 이미 적용된 migration은 절대 수정하지 않는다.
- 새 migration 파일을 생성한다.
- constraint/index 이름은 deterministic naming 규칙을 따른다.

## 테스트 import 경계 규칙
- 다른 domain의 `models` 직접 import 금지 (`migrations/` 예외)
- 다른 domain 내부 모듈 직접 import 금지
- 다른 domain이 필요하면 `services/__init__.py` facade 또는 `selectors.py` 사용

## 실행 명령
```bash
# 전체 테스트
docker compose -f docker-compose.dev.yml exec -T api python manage.py test

# 특정 앱 테스트
docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.<feature>

# migration 생성/적용
docker compose -f docker-compose.dev.yml exec -T api python manage.py makemigrations
docker compose -f docker-compose.dev.yml exec -T api python manage.py migrate
```

## 작업 절차
1. 변경 유형 분류
   - schema change / business logic change / read query change / HTTP contract change
2. 필요한 테스트 범위 결정
   - service / selector / minimal view
3. migration 필요 여부 확인
4. 경계 위반 점검
   - cross-domain 내부 import 여부
   - selector write 여부
   - view ORM read 여부
5. 컨테이너 기준 실행 명령 제안 또는 수행

## 출력 규칙
응답에 가능한 한 아래를 포함한다.

- 추가/수정할 테스트 범위
- migration 필요 여부
- 실행할 명령
- 위험 포인트

## 금지사항
- host Python dependency 설치를 전제로 안내하지 않는다.
- view test를 과도하게 두껍게 만들지 않는다.
- migration history를 rewrite하지 않는다.
