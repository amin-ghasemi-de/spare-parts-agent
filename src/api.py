from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.agent import run_agent
from src.case_store import Case, approve_case, create_case, list_cases, load_case, reject_case
from src.config import PROJECT_ROOT

EMAIL_DIR = PROJECT_ROOT / "data" / "emails"
FRONTEND_DIR = PROJECT_ROOT / "frontend" / "dist"

app = FastAPI(title="Spare-Parts Request Agent")


class ProcessRequest(BaseModel):
    email_text: str = Field(min_length=20, max_length=10000)


class ApproveRequest(BaseModel):
    final_reply: str = Field(min_length=1)
    note: str | None = None


class RejectRequest(BaseModel):
    note: str | None = None


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/sample-emails")
def sample_emails() -> list[dict]:
    emails = []
    for path in sorted(EMAIL_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        subject = text.splitlines()[0].removeprefix("Subject:").strip()
        emails.append({"name": path.name, "subject": subject, "text": text})
    return emails


@app.post("/api/cases")
def process_email(request: ProcessRequest) -> Case:
    try:
        result = run_agent(request.email_text)
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Agent failed: {error}") from error
    return create_case(request.email_text, result)


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


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")