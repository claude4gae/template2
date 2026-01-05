# =============================================================================
# 모듈 설명: API 공용 DB 헬퍼 함수를 제공합니다.
# - 주요 대상: run_query, execute, get_cursor
# - 불변 조건: SQL/파라미터는 호출자가 안전하게 제공해야 합니다.
# =============================================================================

"""API에서 사용하는 데이터베이스 헬퍼 함수 모음.

- 주요 대상: run_query, execute, get_cursor
- 주요 엔드포인트/클래스: 없음(함수형 헬퍼만 제공)
- 가정/불변 조건: 호출자는 SQL과 파라미터를 안전하게 제공해야 함
"""
from __future__ import annotations

from contextlib import contextmanager  # with 문에서 자원 자동 정리용
from typing import Iterator, List, Optional, Sequence

from django.db import connection  # Django의 DB 연결 객체 (커서 획득용)
from django.db.backends.utils import CursorWrapper


def _dictfetchall(cursor) -> List[dict]:
    """커서의 결과 행을 딕셔너리 리스트로 변환합니다.

    입력:
    - cursor: DB 커서 객체

    반환:
    - List[dict]: {"컬럼명": 값, ...} 형태의 결과 목록

    부작용:
    - 없음

    오류:
    - 없음(커서 상태 오류는 상위 예외가 전파됨)
    """
    # cursor.description 은 SELECT 결과의 컬럼 정보 목록
    columns = [col[0] for col in cursor.description] if cursor.description else []
    # zip(columns, row)로 컬럼명-값 쌍을 묶어 dict 생성
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


@contextmanager
def get_cursor() -> Iterator[CursorWrapper]:
    """데이터베이스 커서를 안전하게 열고 닫는 컨텍스트 매니저입니다.

    입력:
    - 없음

    반환:
    - cursor: Django DB 커서 객체

    부작용:
    - 컨텍스트 종료 시 커서가 자동으로 close됨

    오류:
    - 없음(커서 생성 실패는 상위 예외가 전파됨)
    """
    with connection.cursor() as cursor:  # 테스트 제외(커버리지): pragma: no cover
        yield cursor


def run_query(sql: str, params: Optional[Sequence[object]] = None) -> List[dict]:
    """SELECT 계열 쿼리를 실행하고 결과를 딕셔너리 리스트로 반환합니다.

    입력:
    - sql: 실행할 SQL 문자열
    - params: 바인딩 파라미터 목록

    반환:
    - List[dict]: 결과 행 목록

    부작용:
    - DB 읽기 쿼리 수행

    오류:
    - 없음(쿼리 실패 시 상위 예외가 전파됨)
    """
    with get_cursor() as cursor:
        cursor.execute(sql, params or [])
        return _dictfetchall(cursor)


def execute(sql: str, params: Optional[Sequence[object]] = None) -> tuple[int, Optional[int]]:
    """INSERT/UPDATE/DELETE 계열 쿼리를 실행합니다.

    입력:
    - sql: 실행할 SQL 문자열
    - params: 바인딩 파라미터 목록

    반환:
    - tuple[int, Optional[int]]: (영향 행 수, 마지막 생성 PK)

    부작용:
    - DB 쓰기 쿼리 수행

    오류:
    - 없음(쿼리 실패 시 상위 예외가 전파됨)
    """
    with get_cursor() as cursor:
        # -----------------------------------------------------------------------------
        # 1) 쿼리 실행
        # -----------------------------------------------------------------------------
        cursor.execute(sql, params or [])
        lastrowid = None

        # -----------------------------------------------------------------------------
        # 2) 결과 행 처리(RETURNING 등)
        # -----------------------------------------------------------------------------
        if cursor.description:
            try:
                row = cursor.fetchone()
            except Exception:  # 방어 코드: 결과가 비정상일 경우
                row = None
            if row:
                lastrowid = row[0]
        else:
            # SQLite/MySQL의 lastrowid 속성 사용
            lastrowid = getattr(cursor, "lastrowid", None)

        # -----------------------------------------------------------------------------
        # 3) 결과 반환
        # -----------------------------------------------------------------------------
        return cursor.rowcount, lastrowid
