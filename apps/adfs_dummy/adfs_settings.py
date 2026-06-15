"""더미 ADFS/RAG FastAPI 서버를 위한 공용 설정입니다.

환경변수 파싱을 이곳에 모아 두어 각 라우터가 요청 처리에 집중하도록 합니다.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, List, Sequence


def parse_env_list(name: str, fallback: Sequence[str]) -> List[str]:
    raw = os.getenv(name)
    if not raw:
        return list(fallback)

    parsed: Any = None
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        parsed = None

    if isinstance(parsed, Sequence) and not isinstance(parsed, (str, bytes, bytearray)):
        values = [str(item).strip() for item in parsed if str(item).strip()]
        if values:
            return values

    values = [item.strip() for item in str(raw).split(",") if item.strip()]
    return values or list(fallback)


def parse_env_int(name: str, fallback: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return fallback
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        return fallback


def parse_env_bool(name: str, fallback: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return fallback
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


APP_TITLE = "Dummy ADFS"
APP_VERSION = "2.1.0"

CLIENT_ID = os.getenv("DUMMY_ADFS_CLIENT_ID", "dummy-client")
DEFAULT_EMAIL = os.getenv("DUMMY_ADFS_EMAIL", "dummy.user@example.com")
DEFAULT_NAME = os.getenv("DUMMY_ADFS_NAME", "Dummy User")
DEFAULT_DEPT = os.getenv("DUMMY_ADFS_DEPT", "Development")
DEFAULT_SABUN = os.getenv("DUMMY_ADFS_SABUN", "S000001")
DEFAULT_LOGINID = os.getenv("DUMMY_ADFS_LOGINID") or (
    DEFAULT_EMAIL.split("@")[0] if "@" in DEFAULT_EMAIL else DEFAULT_EMAIL
)
DEFAULT_DEPTID = os.getenv("DUMMY_ADFS_DEPTID", "D000000")
DEFAULT_USERNAME_EN = os.getenv("DUMMY_ADFS_USERNAME_EN", "Dummy User")
DEFAULT_GIVENNAME = os.getenv("DUMMY_ADFS_GIVENNAME", "Dummy")
DEFAULT_SURNAME = os.getenv("DUMMY_ADFS_SURNAME", "User")
DEFAULT_GRDNAME = os.getenv("DUMMY_ADFS_GRDNAME", "Engineer")
DEFAULT_GRDNAME_EN = os.getenv("DUMMY_ADFS_GRDNAME_EN", "Engineer")
DEFAULT_BUSNAME = os.getenv("DUMMY_ADFS_BUSNAME", "Development")
DEFAULT_INTCODE = os.getenv("DUMMY_ADFS_INTCODE", "INT000")
DEFAULT_INTNAME = os.getenv("DUMMY_ADFS_INTNAME", "Internal")
DEFAULT_ORIGINCOMP = os.getenv("DUMMY_ADFS_ORIGINCOMP", "LOCAL")
DEFAULT_EMPLOYEETYPE = os.getenv("DUMMY_ADFS_EMPLOYEETYPE", "employee")
DEFAULT_CLIENT_IP = os.getenv("DUMMY_ADFS_CLIENT_IP", "127.0.0.1")
AUTO_SIGN_IN = parse_env_bool("DUMMY_ADFS_AUTO_SIGN_IN", False)

ISSUER = os.getenv("DUMMY_ADFS_ISSUER", "http://localhost:9000/adfs")
PRIVATE_KEY_PATH = Path(os.getenv("DUMMY_ADFS_PRIVATE_KEY_PATH", "dummy_adfs_private.key")).resolve()
LOGOUT_REDIRECT = os.getenv("DUMMY_ADFS_LOGOUT_TARGET", "http://localhost")

DEFAULT_PERMISSION_GROUPS = parse_env_list("DUMMY_RAG_PERMISSION_GROUPS", ["rag-public"])

DUMMY_LLM_REPLY_TEMPLATE = os.getenv(
    "DUMMY_LLM_REPLY_TEMPLATE",
    '개발용 더미 응답입니다. 질문 "{question}" 에 대한 테스트 답변입니다.',
)
DUMMY_LLM_DELAY_MS = parse_env_int("DUMMY_LLM_DELAY_MS", 0)

RAG_INDEX_DEFAULT = (
    os.getenv("DUMMY_RAG_INDEX_NAME")
    or os.getenv("RAG_INDEX_DEFAULT")
    or os.getenv("RAG_INDEX_NAME")
    or "rp-unclassified"
)
RAG_INDEX_EMAILS = os.getenv("RAG_INDEX_EMAILS") or "rp-emails"
RAG_INDEX_LIST = parse_env_list("RAG_INDEX_LIST", [])
PRIMARY_RAG_INDEX = RAG_INDEX_DEFAULT
ASSISTANT_RAG_INDEX = os.getenv("DUMMY_ASSISTANT_RAG_INDEX") or os.getenv("ASSISTANT_RAG_INDEX_NAME") or PRIMARY_RAG_INDEX
EXTRA_RAG_INDEXES = parse_env_list("DUMMY_RAG_INDEXES", [])

INDEX_NAMES: List[str] = []
for name in [*RAG_INDEX_LIST, PRIMARY_RAG_INDEX, ASSISTANT_RAG_INDEX, *EXTRA_RAG_INDEXES]:
    if name and name not in INDEX_NAMES:
        INDEX_NAMES.append(name)
if not INDEX_NAMES:
    INDEX_NAMES.append("emails")

MAILBOX_RAG_INDEX = os.getenv("DUMMY_MAIL_RAG_INDEX") or RAG_INDEX_EMAILS or PRIMARY_RAG_INDEX or INDEX_NAMES[0]
if MAILBOX_RAG_INDEX not in INDEX_NAMES:
    INDEX_NAMES.append(MAILBOX_RAG_INDEX)

try:
    PRIVATE_KEY = PRIVATE_KEY_PATH.read_text(encoding="utf-8")
except OSError as exc:  # 개발용 피드백(커버리지 제외): pragma: no cover
    raise RuntimeError(f"Failed to read dummy ADFS private key: {PRIVATE_KEY_PATH}") from exc
