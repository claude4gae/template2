---
name: write-commented-python
description: |
  Django backend 코드에 한국어 주석과 docstring을 일관되게 추가하는 스킬.
  service, selector, view, serializer 등 설명형 코드를 생성할 때 사용한다.
---

# write-commented-python

## 목적
backend 코드를 초보자도 단계적으로 읽을 수 있게 설명형으로 작성한다.

## 사용할 때
- 사용자가 "주석 달아줘", "설명 포함", "전체 코드 다시 줘"를 요청할 때
- request parsing/validation/permission checks가 있는 view를 작성할 때
- upsert/dedupe/timezone conversion/pagination 등 비단순 로직이 있을 때
- 함수/메서드가 길거나 분기가 많은 경우
- public service/selector/view method를 생성할 때

## 언어 규칙
- 모든 주석과 docstring은 한국어로 작성한다.
- Proper noun은 원문을 유지한다.
- 외부 spec상 영어가 필요하면 한국어를 먼저 쓰고 영어를 병기한다.

## 기본 문서화 규칙
1. 모듈 헤더
   - 파일 목적
   - 주요 클래스/함수
   - 핵심 전제/불변조건
2. public 함수/메서드 docstring
   - 무엇을 하는지
   - 입력값
   - 반환값
   - side effect
   - 발생 가능한 예외/오류 조건
3. 복잡한 함수 단계 주석
   - 아래 형식을 사용한다.

```python
# -----------------------------------------------------------------------------
# 1) 요청 파싱
# -----------------------------------------------------------------------------
```

4. inline comment 원칙
   - 주석은 "왜"를 설명한다.
   - 코드가 드러내는 "무엇"을 반복 설명하지 않는다.

## View 전용 규칙
APIView/endpoint docstring에는 최소 1개의 예시를 넣는다.

- request payload 예시 또는 query param 예시
- snake_case / camelCase compatibility 여부(지원 시)

## comment density 기준
- logical block 단위로 의미 있는 주석을 넣는다.
- 너무 듬성듬성하거나 과도하게 장황하지 않게 유지한다.
- 권장 밀도: 5~15줄당 의미 있는 주석 1개 수준

## 파일 섹션 템플릿
- 복잡한 파일은 주요 섹션을 아래 구분선으로 나눈다.

```python
# =============================================================================
# <섹션 제목>
# =============================================================================
```

- 상수는 timezone/constants/pagination 등 목적별로 묶어 라벨링한다.

## 금지사항
- 코드와 모순되는 주석
- assistant 메타 설명
- 과거 이력 중심 주석
- 자명한 코드를 한 줄마다 반복 설명

## 출력 방식
설명형 Python 코드 출력 시 가능하면 아래 순서를 따른다.

1. 파일 경로
2. 파일 역할 요약
3. 변경된 핵심 부분 snippet
4. 필요 시 핵심 흐름 요약

전체 코드는 사용자가 명시적으로 요청한 경우에만 출력한다.
기본 응답은 `safe-file-edit-output` 규칙을 우선 적용한다.

## 우선 적용 대상
- `services/__init__.py`
- `services/*`
- `selectors.py`
- `views.py`
