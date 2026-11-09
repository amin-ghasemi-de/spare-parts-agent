import re
import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel

from src.agent import AgentResult
from src.config import PROJECT_ROOT

CASES_DIR = PROJECT_ROOT / "storage" / "cases"
OUTBOX_DIR = PROJECT_ROOT / "outbox"


class Case(BaseModel):
    id: str
    created_at: str
    email_text: str
    source: str | None = None
    reply_to: str | None = None
    subject: str | None = None
    result: AgentResult
    status: Literal["pending_review", "approved", "rejected"] = "pending_review"
    final_reply: str | None = None
    edited_by_human: bool = False
    reviewer_note: str | None = None
    decided_at: str | None = None
    sent_at: str | None = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def save_case(case: Case) -> None:
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    (CASES_DIR / f"{case.id}.json").write_text(case.model_dump_json(indent=2), encoding="utf-8")


def create_case(
    email_text: str,
    result: AgentResult,
    source: str | None = None,
    reply_to: str | None = None,
    subject: str | None = None,
) -> Case:
    case = Case(
        id=uuid.uuid4().hex[:8],
        created_at=_now(),
        email_text=email_text,
        source=source,
        reply_to=reply_to,
        subject=subject,
        result=result,
    )
    save_case(case)
    return case


def load_case(case_id: str) -> Case | None:
    if not re.fullmatch(r"[0-9a-f]{8}", case_id):
        return None
    path = CASES_DIR / f"{case_id}.json"
    if not path.exists():
        return None
    return Case.model_validate_json(path.read_text(encoding="utf-8"))


def list_cases() -> list[Case]:
    if not CASES_DIR.exists():
        return []
    cases = [Case.model_validate_json(path.read_text(encoding="utf-8")) for path in CASES_DIR.glob("*.json")]
    return sorted(cases, key=lambda case: case.created_at, reverse=True)


def approve_case(case: Case, final_reply: str, note: str | None = None) -> Case:
    case.status = "approved"
    case.final_reply = final_reply
    case.edited_by_human = final_reply.strip() != (case.result.draft or "").strip()
    case.reviewer_note = note
    case.decided_at = _now()
    save_case(case)

    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    (OUTBOX_DIR / f"{case.id}.txt").write_text(final_reply, encoding="utf-8")
    return case


def reject_case(case: Case, note: str | None = None) -> Case:
    case.status = "rejected"
    case.reviewer_note = note
    case.decided_at = _now()
    save_case(case)
    return case


def mark_sent(case: Case) -> Case:
    case.sent_at = _now()
    save_case(case)
    return case