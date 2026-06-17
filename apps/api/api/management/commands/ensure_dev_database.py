# =============================================================================
# 모듈 설명: dev 환경에서 Django 기본 DB 존재를 보장하는 command를 제공합니다.
# - 주요 클래스: Command
# - 불변 조건: ENVIRONMENT=development 에서만 DB 생성을 시도합니다.
# =============================================================================

from __future__ import annotations

import os
from typing import Any

import psycopg
from psycopg import sql

from django.core.management.base import BaseCommand, CommandError

REQUIRED_EXTENSIONS = ("pg_trgm",)


def _env(name: str, default: str = "") -> str:
    """환경변수 문자열 값을 공백 제거 후 반환합니다."""

    return (os.getenv(name) or default).strip()


def _ensure_development_environment() -> None:
    """개발 환경에서만 DB bootstrap을 허용합니다."""

    environment = _env("ENVIRONMENT").lower()
    if environment != "development":
        raise CommandError("ensure_dev_database는 ENVIRONMENT=development 에서만 실행할 수 있습니다.")


def _build_connection_kwargs(*, database_name: str) -> dict[str, str]:
    """psycopg 접속 인자를 Django DB env 기준으로 구성합니다."""

    return {
        "dbname": database_name,
        "user": _env("DJANGO_DB_USER") or _env("DB_USER", "airflow"),
        "password": _env("DJANGO_DB_PASSWORD") or _env("DB_PASSWORD", "airflow"),
        "host": _env("DJANGO_DB_HOST") or _env("DB_HOST", "airflow-postgres"),
        "port": _env("DJANGO_DB_PORT") or _env("DB_PORT", "8010"),
    }


def _database_exists(cursor: Any, *, database_name: str) -> bool:
    """PostgreSQL catalog에서 대상 DB 존재 여부를 확인합니다."""

    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", [database_name])
    return cursor.fetchone() is not None


def _create_database(cursor: Any, *, database_name: str, owner: str) -> None:
    """대상 DB를 안전하게 quote하여 생성합니다."""

    cursor.execute(
        sql.SQL("CREATE DATABASE {} OWNER {}").format(
            sql.Identifier(database_name),
            sql.Identifier(owner),
        )
    )


def _ensure_required_extensions(*, database_name: str) -> None:
    """Django migration에 필요한 PostgreSQL extension을 보장합니다."""

    connection_kwargs = _build_connection_kwargs(database_name=database_name)
    with psycopg.connect(**connection_kwargs, autocommit=True) as connection:
        with connection.cursor() as cursor:
            for extension_name in REQUIRED_EXTENSIONS:
                cursor.execute(
                    sql.SQL("CREATE EXTENSION IF NOT EXISTS {}").format(
                        sql.Identifier(extension_name),
                    )
                )


class Command(BaseCommand):
    """dev 환경에서 Django 기본 DB와 필수 extension을 보장합니다."""

    help = "Ensure the Django development database and required extensions exist before running migrations."

    def add_arguments(self, parser) -> None:
        """커맨드 인자를 정의합니다."""

        parser.add_argument(
            "--database",
            default=_env("DJANGO_DB_NAME") or _env("DB_NAME", "dashboard"),
            help="생성 여부를 확인할 Django DB 이름",
        )
        parser.add_argument(
            "--maintenance-database",
            default=_env("DJANGO_DB_MAINTENANCE_NAME", "airflow"),
            help="DB 생성 쿼리를 실행할 maintenance DB 이름",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Django 기본 DB가 없으면 생성하고 결과를 출력합니다."""

        _ensure_development_environment()

        target_database = str(options["database"] or "").strip()
        maintenance_database = str(options["maintenance_database"] or "").strip()
        if not target_database:
            raise CommandError("--database must not be empty")
        if not maintenance_database:
            raise CommandError("--maintenance-database must not be empty")

        if target_database == maintenance_database:
            self.stdout.write(f"[db-bootstrap] target database already matches maintenance database: {target_database}")
        else:
            connection_kwargs = _build_connection_kwargs(database_name=maintenance_database)
            owner = connection_kwargs["user"]
            try:
                with psycopg.connect(**connection_kwargs, autocommit=True) as connection:
                    with connection.cursor() as cursor:
                        if _database_exists(cursor, database_name=target_database):
                            self.stdout.write(f"[db-bootstrap] database exists: {target_database}")
                        else:
                            _create_database(cursor, database_name=target_database, owner=owner)
                            self.stdout.write(self.style.SUCCESS(f"[db-bootstrap] database created: {target_database}"))
            except psycopg.Error as exc:
                raise CommandError(f"개발 DB 생성 확인에 실패했습니다: {exc}") from exc

        try:
            _ensure_required_extensions(database_name=target_database)
        except psycopg.Error as exc:
            raise CommandError(f"개발 DB extension 확인에 실패했습니다: {exc}") from exc

        self.stdout.write(f"[db-bootstrap] extensions ensured: {', '.join(REQUIRED_EXTENSIONS)}")
