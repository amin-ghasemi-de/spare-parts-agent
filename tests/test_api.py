import pytest
from fastapi.testclient import TestClient

import src.api as api
import src.case_store as case_store
from src.agent import AgentResult
from src.schemas import SparePartRequest

EMAIL_TEXT = "Subject: Test\n\nWir brauchen 2 Stück Kolbenringsatz HPC-SEA-110."


def fake_run_agent(email_text: str) -> AgentResult:
    extraction = SparePartRequest(is_spare_part_request=True, language="de")
    return AgentResult(extraction=extraction, draft="Guten Tag, hier ist unser Angebot.", status="finished")


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(case_store, "CASES_DIR", tmp_path / "cases")
    monkeypatch.setattr(case_store, "OUTBOX_DIR", tmp_path / "outbox")
    monkeypatch.setattr(api, "run_agent", fake_run_agent)
    return TestClient(api.app)


def create_case(client: TestClient) -> dict:
    response = client.post("/api/cases", json={"email_text": EMAIL_TEXT})
    assert response.status_code == 200
    return response.json()


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_inbox_lists_unprocessed_emails(client):
    emails = client.get("/api/inbox").json()
    assert len(emails) >= 5
    assert emails[0]["name"] == "email_001.txt"
    assert emails[0]["sender"].startswith("Markus Weber")


def test_processed_inbox_email_leaves_the_inbox(client):
    before = len(client.get("/api/inbox").json())
    response = client.post("/api/inbox/email_001.txt/process")
    assert response.status_code == 200
    assert response.json()["source"] == "email_001.txt"

    names = [email["name"] for email in client.get("/api/inbox").json()]
    assert "email_001.txt" not in names
    assert len(names) == before - 1


def test_inbox_email_cannot_be_processed_twice(client):
    client.post("/api/inbox/email_001.txt/process")
    response = client.post("/api/inbox/email_001.txt/process")
    assert response.status_code == 409


def test_unknown_inbox_email_returns_404(client):
    assert client.post("/api/inbox/does_not_exist.txt/process").status_code == 404
    assert client.post("/api/inbox/secret.env/process").status_code == 404


def test_new_case_waits_for_review(client):
    case = create_case(client)
    assert case["status"] == "pending_review"
    assert case["result"]["draft"].startswith("Guten Tag")


def test_approve_with_edit_writes_outbox(client, tmp_path):
    case = create_case(client)
    response = client.post(f"/api/cases/{case['id']}/approve", json={"final_reply": "Edited reply"})
    approved = response.json()
    assert approved["status"] == "approved"
    assert approved["edited_by_human"] is True
    assert (tmp_path / "outbox" / f"{case['id']}.txt").read_text(encoding="utf-8") == "Edited reply"


def test_case_cannot_be_decided_twice(client):
    case = create_case(client)
    client.post(f"/api/cases/{case['id']}/reject", json={"note": "wrong part"})
    response = client.post(f"/api/cases/{case['id']}/approve", json={"final_reply": "x"})
    assert response.status_code == 409


def test_unknown_or_invalid_case_id_returns_404(client):
    assert client.get("/api/cases/00000000").status_code == 404
    assert client.get("/api/cases/..%2F..%2Fsecret").status_code == 404


def test_too_short_email_is_rejected(client):
    response = client.post("/api/cases", json={"email_text": "hi"})
    assert response.status_code == 422

def test_external_email_is_stored_with_reply_address_and_not_processed_twice(client):
    payload = {
        "email_text": EMAIL_TEXT,
        "source": "imap:12345",
        "reply_to": "customer@example.com",
        "subject": "Ersatzteile",
    }
    case = client.post("/api/cases", json=payload).json()
    assert case["reply_to"] == "customer@example.com"
    assert case["source"] == "imap:12345"
    assert client.post("/api/cases", json=payload).status_code == 409


def test_outbox_lists_only_approved_unsent_cases_and_mark_sent_works(client):
    payload = {"email_text": EMAIL_TEXT, "reply_to": "customer@example.com", "subject": "Ersatzteile"}
    approved = client.post("/api/cases", json=payload).json()
    pending = client.post("/api/cases", json=payload).json()
    pasted = client.post("/api/cases", json={"email_text": EMAIL_TEXT}).json()
    client.post(f"/api/cases/{approved['id']}/approve", json={"final_reply": "Final text"})
    client.post(f"/api/cases/{pasted['id']}/approve", json={"final_reply": "No address"})

    outbox = client.get("/api/outbox").json()
    assert [item["id"] for item in outbox] == [approved["id"]]
    assert outbox[0] == {
        "id": approved["id"],
        "reply_to": "customer@example.com",
        "subject": "Re: Ersatzteile",
        "body": "Final text",
    }

    assert client.post(f"/api/cases/{pending['id']}/mark-sent").status_code == 409
    sent = client.post(f"/api/cases/{approved['id']}/mark-sent").json()
    assert sent["sent_at"] is not None
    assert client.get("/api/outbox").json() == []
    assert client.post(f"/api/cases/{approved['id']}/mark-sent").status_code == 409