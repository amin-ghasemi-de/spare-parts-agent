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


def test_sample_emails_are_listed(client):
    emails = client.get("/api/sample-emails").json()
    assert len(emails) == 5
    assert emails[0]["name"] == "email_001.txt"


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