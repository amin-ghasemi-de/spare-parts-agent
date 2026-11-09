import re
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.agent import run_agent
from src.case_store import Case, approve_case, create_case, list_cases, load_case, mark_sent, reject_case
from src.config import PROJECT_ROOT

EMAIL_DIR = PROJECT_ROOT / "data" / "emails"
FRONTEND_DIR = PROJECT_ROOT / "frontend" / "dist"
INBOX_NAME_PATTERN = re.compile(r"[\w\-]+\.txt")

app = FastAPI(title="Spare-Parts Request Agent")


class ProcessRequest(BaseModel):
    email_text: str = Field(min_length=20, max_length=10000)
    source: str | None = Field(default=None, max_length=300)
    reply_to: str | None = Field(default=None, max_length=300)
    subject: str | None = Field(default=None, max_length=300)


class ApproveRequest(BaseModel):
    final_reply: str = Field(min_length=1)
    note: str | None = None


class RejectRequest(BaseModel):
    note: str | None = None


def _read_inbox_email(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    subject = lines[0].removeprefix("Subject:").strip() if lines else path.name
    sender = next((line.removeprefix("From:").strip() for line in lines if line.startswith("From:")), None)
    return {"name": path.name, "subject": subject, "sender": sender, "text": text}


def _processed_emails() -> tuple[set[str], set[str]]:
    cases = list_cases()
    sources = {case.source for case in cases if case.source}
    texts = {case.email_text.strip() for case in cases}
    return sources, texts


def _run_and_create_case(
    email_text: str,
    source: str | None = None,
    reply_to: str | None = None,
    subject: str | None = None,
) -> Case:
    try:
        result = run_agent(email_text)
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Agent failed: {error}") from error
    return create_case(email_text, result, source=source, reply_to=reply_to, subject=subject)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/inbox")
def inbox() -> list[dict]:
    sources, texts = _processed_emails()
    emails = []
    for path in sorted(EMAIL_DIR.glob("*.txt")):
        email = _read_inbox_email(path)
        if path.name in sources or email["text"].strip() in texts:
            continue
        emails.append(email)
    return emails


@app.post("/api/inbox/{name}/process")
def process_inbox_email(name: str) -> Case:
    path = EMAIL_DIR / name
    if not INBOX_NAME_PATTERN.fullmatch(name) or not path.exists():
        raise HTTPException(status_code=404, detail="E-mail not found")

    email_text = path.read_text(encoding="utf-8")
    sources, texts = _processed_emails()
    if name in sources or email_text.strip() in texts:
        raise HTTPException(status_code=409, detail="E-mail was already processed")

    return _run_and_create_case(email_text, source=name)


@app.post("/api/cases")
def process_email(request: ProcessRequest) -> Case:
    if request.source and request.source in _processed_emails()[0]:
        raise HTTPException(status_code=409, detail="E-mail was already processed")
    return _run_and_create_case(request.email_text, request.source, request.reply_to, request.subject)


@app.get("/api/cases")
def get_cases() -> list[Case]:
    return list_cases()


def _get_case_or_404(case_id: str) -> Case:
    case = load_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@app.get("/api/cases/{case_id}")
def get_case(case_id: str) -> Case:
    return _get_case_or_404(case_id)


@app.post("/api/cases/{case_id}/approve")
def approve(case_id: str, request: ApproveRequest) -> Case:
    case = _get_case_or_404(case_id)
    if case.status != "pending_review":
        raise HTTPException(status_code=409, detail=f"Case is already {case.status}")
    return approve_case(case, request.final_reply, request.note)


@app.post("/api/cases/{case_id}/reject")
def reject(case_id: str, request: RejectRequest) -> Case:
    case = _get_case_or_404(case_id)
    if case.status != "pending_review":
        raise HTTPException(status_code=409, detail=f"Case is already {case.status}")
    return reject_case(case, request.note)


@app.get("/api/outbox")
def outbox() -> list[dict]:
    ready = [
        case
        for case in list_cases()
        if case.status == "approved" and not case.sent_at and case.reply_to
    ]
    return [
        {
            "id": case.id,
            "reply_to": case.reply_to,
            "subject": f"Re: {case.subject}" if case.subject else "Your spare-parts request",
            "body": case.final_reply,
        }
        for case in ready
    ]


@app.post("/api/cases/{case_id}/mark-sent")
def mark_case_sent(case_id: str) -> Case:
    case = _get_case_or_404(case_id)
    if case.status != "approved":
        raise HTTPException(status_code=409, detail="Only approved cases can be sent")
    if case.sent_at:
        raise HTTPException(status_code=409, detail="Case was already sent")
    return mark_sent(case)


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")