# ExecPlan: Drone 메일 템플릿 독립화

## 목표
- Drone 메일 템플릿 파일별로 제목 생성과 본문 HTML을 독립적으로 소유한다.
- 메일 경로에서는 `summary` 용어 대신 `subject` 용어를 사용한다.

## 변경 전 상태
- `mail_template_common.py`, `mail_template_h1.py`는 제목 생성 일부를 Jira 템플릿에서 가져오고 본문은 `mail_template_body.py`를 공유했다.
- `mail_template_auto_sp.py`는 본문을 자체 보유하지만 제목 생성 함수명이 `build_summary`였다.
- 메일 발송기는 registry에서 제목 builder와 본문 source를 조회했다.

## 범위
- 수정: `apps/api/api/drone/services/mail/**`, 관련 Drone 테스트.
- 수정하지 않음: Jira 템플릿, DB schema, API/env/auth contract.

## 설계
- 각 `mail_template_*.py`는 `TEMPLATE_KEY`, `SUBJECT_TEMPLATE`, `BODY_TEMPLATE`, `build_subject`를 제공한다.
- `mail_template_registry.py`는 `MAIL_SUBJECT_BUILDERS`와 `MAIL_TEMPLATE_SOURCES`를 등록한다.
- `mail_sender.py`는 메일 subject builder registry만 참조한다.
- 기존 `mail_template_key` 값(`common`, `H1`, `auto_sp`)은 유지한다.

## 실행 단계
- [x] 템플릿 파일별 subject/body 독립화
- [x] registry와 sender 용어를 subject로 정리
- [x] 테스트를 새 subject contract 기준으로 갱신
- [x] 컨테이너 기준 검증 실행

## 검증
- `docker compose -f docker-compose.dev.yml run --rm --entrypoint python api -m compileall api/drone/services/mail api/drone/tests.py`
- `docker compose -f docker-compose.dev.yml run --rm --entrypoint python api -c "...subject registry smoke..."`
- Django test는 로컬 DB/extension 상태에 따라 실행 가능 여부를 기록한다.

## 위험과 대응
- 위험: 기존 common/h1 제목 출력이 바뀔 수 있다.
- 대응: 기존 로직을 메일 템플릿 내부로 옮기되 결과 문자열은 유지한다.

## 진행 기록
- 2026-06-12: Auto S/P 추가 후 템플릿 독립화 방향으로 리팩터링 시작.
- 2026-06-12: `common`, `H1`, `auto_sp` 메일 템플릿이 각자 `build_subject`와 `BODY_TEMPLATE`를 가지도록 정리.
- 2026-06-12: `compileall`과 subject registry smoke 검증 통과. Django test는 로컬 테스트 DB의 `pg_trgm` 확장 부재로 migration 단계에서 실패.
- 2026-06-12: `common` 메일 제목/registry 테스트를 추가하고 완료된 상태에 맞게 계획 문구를 정리.
