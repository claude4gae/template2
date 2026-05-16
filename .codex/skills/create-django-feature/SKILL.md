---
name: create-django-feature
description: |
  새로운 Django 도메인 feature(app)를 저장소 규칙에 맞게 생성하는 스킬.
  app 생성부터 models, serializers, selectors, services, views, urls, tests까지
  정해진 순서로 scaffold한다.
---

# create-django-feature

## 목적
새로운 backend feature를 추가할 때 modular monolith / domain app 규칙을 일관되게 적용한다.

## 사용할 때
- 새로운 backend domain feature를 추가할 때
- root-level 또는 잘못된 위치의 로직을 feature app으로 이전할 때
- feature 단위 API route scope를 추가할 때

## 전제 규칙
- feature app 경로: `apps/api/api/<feature>`
- Django app name: `api.<feature>`
- 허용 파일/폴더만 생성한다.
- 기본 폴더 깊이 최대 2를 지키고, `services/`, `migrations/`, `management/commands/`만 예외로 둔다.
- business logic: `services/`
- read query: `selectors.py`
- HTTP wiring: `views.py`
- global routing: `apps/api/api/urls.py`에서 `include()`만 사용
- cross-feature import는 타 feature의 `services/__init__.py` facade 또는 `selectors.py`만 사용한다.
- legacy root model(`apps/api/api/models.py`)을 건드려야 하면 확장하지 말고 feature app으로 이전 + 신규 migration으로 처리한다.

## 생성 순서 (고정)
순서를 바꾸지 않는다.

1. 앱 경로 생성
   - `apps/api/api/<feature>/`
   - 기본 파일: `__init__.py`, `apps.py`, `models.py`, `serializers.py`, `selectors.py`, `views.py`, `urls.py`, `tests.py`, `services/__init__.py`
   - 필요 시만 추가: `permissions.py`, `admin.py`, `management/commands/`, `migrations/`
2. `apps.py` 작성
   - `name = "api.<feature>"`
   - app label/class는 feature 기준으로 결정
3. `INSTALLED_APPS` 등록
   - 수정 파일: `apps/api/config/settings.py`
   - `api.<feature>` 추가
4. `models.py` 작성
   - concrete model은 해당 feature의 `models.py`에만 둔다.
   - `db_table = "<feature>_<entity>"`
   - snake_case field, singular PascalCase model
   - 기본 PK: `id (BigAutoField)`
   - UTC timezone-aware timestamp 사용 (`created_at` 권장)
   - index/constraint 이름은 deterministic 규칙으로 작성
     - 기본 패턴: `idx_<table>_<cols>`, `uniq_<table>_<cols>`
     - 길이 제한: 30자 이하
     - 토큰 규칙: `_`로 분리 후 약어 맵 적용(미정의 토큰은 첫 3자, 3자 이하는 유지)
     - 30자 초과 또는 충돌 시: 원본 이름 기반 CRC32 5-hex suffix 추가
     - suffix 추가 시: 길이에 맞게 본문을 왼쪽부터 절단하고 trailing `_` 제거
5. migration 생성
   - applied migration 수정 금지
   - 항상 새 migration 생성
6. `serializers.py` 작성
   - request/response schema + validation only
   - business logic 금지
7. `selectors.py` 작성
   - read-only query만 허용
   - filtering/ordering/annotation 가능
   - side effect 금지
8. `services/__init__.py` 작성
   - public facade 역할
   - create/update/delete, `transaction.atomic()`, 외부 연동, business orchestration 담당
   - 길어지면 `services/*`로 분리
9. `views.py` 작성
   - HTTP 처리만 담당
   - auth/permission/serializer validation/service-selector 호출/response 반환
   - 직접 ORM read 금지
10. `urls.py` 작성
    - feature 내부는 relative path만 사용
    - feature 내부에서 global prefix를 중복 작성하지 않음
    - 예: `path("items/", SomeView.as_view())`
    - 추가 URL 모듈이 필요하면 `<purpose>_urls.py`로 만들고 feature `urls.py`에서 include한다.
11. global api urls 등록
    - 수정 파일: `apps/api/api/urls.py`
    - 예: `path("api/v1/<feature>/", include("api.<feature>.urls"))`
    - route scope는 feature slug와 일치시키는 것을 기본으로 한다(legacy mismatch 확장 금지).
12. `tests.py` 작성
    - 우선순위: services -> selectors -> 최소 view(happy/error)

## index/constraint 약어 맵
필요 시 아래 매핑을 우선 사용한다.

- `account=acc`, `affiliation=aff`, `department=dep`, `line=ln`, `user=usr`, `sdwt=sdw`, `prod=prd`
- `access=acs`, `change=chg`, `external=ext`, `snapshot=snp`, `predicted=pred`, `source=src`
- `updated=upd`, `created=crt`, `effective=eff`
- `appstore=aps`, `comment=cmt`, `parent=par`
- `emails=eml`, `email=eml`, `inbox=inb`, `outbox=out`, `asset=ast`, `sequence=seq`
- `ocr=ocr`, `lock=lk`, `expires=exp`, `status=sts`, `time=tm`, `available=avl`
- `jira=jir`, `template=tmpl`, `knox=knx`, `early=erl`, `inform=inf`
- `chamber=chm`, `main=mn`, `step=stp`, `send=snd`, `category=cat`, `name=nam`, `like=lik`, `recipient=rcp`

## 점검 체크리스트
- feature 외부 import가 facade/selectors 경유인지
- views에 business logic이 없는지
- services에 read query가 직접 들어가지 않았는지
- selectors에 write가 없는지
- global `urls.py`가 registry 역할만 하는지
- table/index/constraint naming이 규칙에 맞는지
- import 방향이 허용 매트릭스를 따르는지
  - `views.py` -> serializers/permissions/services/selectors/api.common
  - `services/*` -> selectors/models/api.common/타 feature services facade
  - `selectors.py` -> models/api.common/타 feature selectors

## 금지사항
- `apps/api/api/models.py` 같은 root model 확장
- cross-feature 내부 모듈 직접 import
- view에서 ORM read 직접 수행
- selector에서 write 수행
- serializer에 business workflow 추가
- applied migration 수정

## 출력 방식
새 feature 생성 제안 시 아래 순서로 출력한다.

1. 생성/수정 파일 목록
2. 파일별 역할 한 줄 설명
3. 핵심 변경 요약 또는 필요한 부분 snippet
4. migration/test 필요 여부

전체 파일 내용은 사용자가 명시적으로 요청한 경우에만 출력한다.
기본 응답은 `safe-file-edit-output` 규칙을 우선 적용한다.
