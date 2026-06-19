"""더미 ADFS/RAG FastAPI 서버용 인메모리 스토어입니다."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from adfs_settings import (
    ASSISTANT_RAG_INDEX,
    DEFAULT_EMAIL,
    DEFAULT_PERMISSION_GROUPS,
    INDEX_NAMES,
    MAILBOX_RAG_INDEX,
    PRIMARY_RAG_INDEX,
)


def merge_title_content(title: str, content: str) -> str:
    parts = [piece.strip() for piece in [title or "", content or ""] if piece and piece.strip()]
    return "\n\n".join(parts)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RagStore:
    def __init__(self, index_names: List[str], default_permission_groups: List[str]) -> None:
        self.default_permission_groups = list(default_permission_groups)
        self.index_docs: Dict[str, Dict[str, Dict[str, Any]]] = {name: {} for name in index_names}

    def _ensure_index(self, index_name: str) -> Dict[str, Dict[str, Any]]:
        if index_name not in self.index_docs:
            self.index_docs[index_name] = {}
        return self.index_docs[index_name]

    def reset(self) -> None:
        for docs in self.index_docs.values():
            docs.clear()

    def seed_base_docs(self, base_docs: List[Dict[str, Any]]) -> None:
        self.reset()
        for entry in base_docs:
            index_name = entry.get("index_name") or INDEX_NAMES[0]
            self.upsert(
                index_name=index_name,
                doc_id=str(entry.get("doc_id") or secrets.token_hex(8)),
                title=entry.get("title") or "",
                content=entry.get("content") or "",
                permission_groups=entry.get("permission_groups") or self.default_permission_groups,
                metadata=entry.get("metadata") or {},
            )

    def upsert(
        self,
        *,
        index_name: str,
        doc_id: str,
        title: str,
        content: str,
        permission_groups: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        index = self._ensure_index(index_name)
        groups = permission_groups or list(self.default_permission_groups)
        stored = {
            "index_name": index_name,
            "doc_id": doc_id,
            "title": title,
            "content": content,
            "merge_title_content": merge_title_content(title, content),
            "permission_groups": groups,
            "metadata": metadata or {},
        }
        index[doc_id] = stored
        return stored

    def delete(self, index_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
        return self.index_docs.get(index_name, {}).pop(doc_id, None)

    def _normalize_meta_set(self, value: Any) -> set[str]:
        if isinstance(value, (list, tuple, set)):
            return {str(item).strip() for item in value if str(item).strip()}
        if value is None:
            return set()
        return {str(value).strip()}

    def _apply_filters(self, docs: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        filtered = docs
        dept_codes = filters.get("department_code") or []
        if isinstance(dept_codes, str):
            dept_codes = [dept_codes]
        dept_set = {str(code).strip() for code in dept_codes if str(code).strip()}
        if dept_set:
            filtered = [
                doc
                for doc in filtered
                if dept_set.intersection(self._normalize_meta_set(doc.get("metadata", {}).get("department_code")))
            ]
        return filtered

    def search(
        self,
        *,
        index_name: str,
        query: str,
        limit: int,
        permission_groups: Optional[List[str]],
        filters: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        docs = list(self.index_docs.get(index_name, {}).values())

        if permission_groups:
            allowed = {str(item).strip() for item in permission_groups if str(item).strip()}
            if allowed:
                docs = [doc for doc in docs if set(doc.get("permission_groups", [])) & allowed]

        if filters:
            docs = self._apply_filters(docs, filters)

        if query:
            lowered = query.lower()
            matched = [doc for doc in docs if lowered in doc["merge_title_content"].lower()]
            if matched:
                docs = matched

        docs.sort(key=lambda doc: doc.get("metadata", {}).get("received_at", ""), reverse=True)
        return docs[:limit]

    def all_docs(self) -> List[Dict[str, Any]]:
        all_docs: List[Dict[str, Any]] = []
        for docs in self.index_docs.values():
            all_docs.extend(docs.values())
        return all_docs

    def index_counts(self) -> Dict[str, int]:
        return {index: len(docs) for index, docs in self.index_docs.items()}

    def total_count(self) -> int:
        return sum(self.index_counts().values())


class MailStore:
    def __init__(self, rag_store: RagStore, rag_index: str) -> None:
        self.mailbox: Dict[int, Dict[str, Any]] = {}
        self._seq = 1
        self._drone_sop_step = 0
        self.rag_store = rag_store
        self.rag_index = rag_index

    def reset(self) -> None:
        self.mailbox.clear()
        self._seq = 1
        self._drone_sop_step = 0
        now = datetime.now(timezone.utc)
        samples = [
            {
                "subject": "[더미] 생산 라인 점검 알림",
                "sender": "alerts@example.com",
                "recipient": DEFAULT_EMAIL,
                "body_text": "주간 생산 라인 점검 예정입니다. 안전 수칙을 확인해주세요.",
                "received_at": now.isoformat(),
            },
            {
                "subject": "[더미] 장비 교체 일정 안내",
                "sender": "maintenance@example.com",
                "recipient": DEFAULT_EMAIL,
                "body_text": "Etch 장비 교체 작업이 예정되어 있습니다. 관련 문서를 확인해주세요.",
                "received_at": (now - timedelta(hours=4)).isoformat(),
            },
        ]
        for sample in samples:
            self.create_mail(register_to_rag=True, **sample)

        self.ensure_drone_sop_mail()

    def ensure_drone_sop_mail(self) -> None:
        """Drone SOP 더미 메일을 항상 1개 유지합니다.

        - drone POP3 ingest 더미 모드에서 호출되는 /mail/messages 조회 시,
          매 호출마다 metro_current_step 이 증가하는 메일이 생성되도록 보장합니다.
        """

        for entry in self.mailbox.values():
            subject = entry.get("subject") or ""
            if isinstance(subject, str) and "[drone_sop]" in subject:
                return

        self._drone_sop_step += 1
        step = f"ST{self._drone_sop_step:03d}"
        status = "COMPLETE" if self._drone_sop_step >= 5 else "IN_PROGRESS"

        html = "\n".join(
            [
                "<data>",
                f"  <line_id>L1</line_id>",
                f"  <sdwt_prod>DUMMY</sdwt_prod>",
                f"  <sample_type>NORMAL</sample_type>",
                f"  <sample_group>DUMMY</sample_group>",
                f"  <eqp_id>EQP1</eqp_id>",
                f"  <chamber_ids>1</chamber_ids>",
                f"  <lot_id>LOT.1</lot_id>",
                f"  <proc_id>PROC</proc_id>",
                f"  <ppid>PPID</ppid>",
                f"  <main_step>MS</main_step>",
                f"  <metro_current_step>{step}</metro_current_step>",
                f"  <metro_steps>{step}</metro_steps>",
                f"  <metro_end_step>ST010</metro_end_step>",
                f"  <status>{status}</status>",
                f"  <knoxid>dummy-knox</knoxid>",
                f"  <user_sdwt_prod>dummy-prod</user_sdwt_prod>",
                f"  <comment>demo@$SETUP_EQP</comment>",
                f"  <defect_url>https://example.com/defect</defect_url>",
                "</data>",
            ]
        )

        self.create_mail(
            subject=f"[drone_sop] Dummy step={step}",
            sender="drone@example.com",
            recipient=DEFAULT_EMAIL,
            body_text=html,
            register_to_rag=False,
        )

    def create_mail(
        self,
        *,
        subject: str,
        sender: str,
        recipient: str,
        body_text: str,
        message_id: Optional[str] = None,
        received_at: Optional[str] = None,
        register_to_rag: bool = True,
        permission_groups: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        mail_id = self._seq
        self._seq += 1
        message_id_value = message_id or f"msg-{mail_id:04d}"
        received_at_value = received_at or now_iso()

        entry = {
            "id": mail_id,
            "message_id": message_id_value,
            "subject": subject,
            "sender": sender,
            "recipient": recipient,
            "body_text": body_text,
            "received_at": received_at_value,
        }
        self.mailbox[mail_id] = entry

        if register_to_rag:
            doc_id = f"email-{mail_id}"
            entry["rag_doc_id"] = doc_id
            rag_metadata = {
                "email_id": mail_id,
                "message_id": message_id_value,
                "sender": sender,
                "recipient": recipient,
                "received_at": received_at_value,
            }
            rag_metadata.update(metadata or {})
            self.rag_store.upsert(
                index_name=self.rag_index,
                doc_id=doc_id,
                title=subject,
                content=body_text,
                permission_groups=permission_groups,
                metadata=rag_metadata,
            )

        return entry

    def delete_mail(self, mail_id: int) -> Dict[str, Any]:
        removed = self.mailbox.pop(mail_id, None)
        rag_removed = None
        if removed and removed.get("rag_doc_id"):
            rag_removed = self.rag_store.delete(self.rag_index, removed["rag_doc_id"])
        return {
            "status": "ok",
            "deleted": bool(removed),
            "docIdRemoved": removed.get("rag_doc_id") if rag_removed else None if removed else None,
        }


rag_store = RagStore(INDEX_NAMES, DEFAULT_PERMISSION_GROUPS)
mail_store = MailStore(rag_store, MAILBOX_RAG_INDEX)


class JiraStore:
    def __init__(self) -> None:
        self._seq = 1
        self.issues: Dict[str, Dict[str, Any]] = {}

    def reset(self) -> None:
        self._seq = 1
        self.issues.clear()

    def create_issue(self, *, project_key: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        key = f"{project_key}-{self._seq}"
        issue_id = str(self._seq)
        self._seq += 1

        issue = {
            "id": issue_id,
            "key": key,
            "self": f"http://dummy-jira/rest/api/2/issue/{issue_id}",
            "fields": fields,
        }
        self.issues[key] = issue
        return issue


jira_store = JiraStore()

BASE_RAG_DOCS = [
    {
        "index_name": PRIMARY_RAG_INDEX,
        "doc_id": "procedure-change",
        "title": "[더미] 공정 변경 보고 절차",
        "content": "공정 변경 시 보고 대상, Observer, 승인 흐름을 정리한 더미 문서입니다.",
        "permission_groups": DEFAULT_PERMISSION_GROUPS,
        "metadata": {"department_code": "FAB-OPS", "source": "dummy-rag"},
    },
    {
        "index_name": ASSISTANT_RAG_INDEX,
        "doc_id": "safety-checklist",
        "title": "[더미] 안전 점검 체크리스트",
        "content": "Etch 설비 점검 시 확인해야 할 항목과 안전 수칙을 정리했습니다.",
        "permission_groups": DEFAULT_PERMISSION_GROUPS,
        "metadata": {"department_code": "SAFETY", "source": "dummy-rag"},
    },
]


def seed_all() -> None:
    """외부 개발 환경의 결정적 실행을 위해 RAG/메일박스 스토어를 초기화합니다."""
    rag_store.seed_base_docs(BASE_RAG_DOCS)
    mail_store.reset()
    jira_store.reset()
