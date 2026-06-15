"""
Integration tests for the FastAPI webhook.

The LLM call itself is monkeypatched so these tests run instantly, need no
network access, and need no API key -- making them safe for CI / grading.
"""

import json

import pytest
from fastapi.testclient import TestClient

from app import main as main_module
from app.main import app
from app.models import TicketIn, TicketOut

client = TestClient(app)


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "running"


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_classify_happy_path(monkeypatch, tmp_path):
    # Redirect prediction logs to a temp file for this test.
    log_file = tmp_path / "predictions.jsonl"
    monkeypatch.setattr(main_module.config, "LOG_FILE", str(log_file))

    async def fake_classify_ticket(ticket: TicketIn) -> TicketOut:
        return TicketOut(
            **ticket.model_dump(),
            category="Network",
            subcategory="VPN Access",
            priority="High",
            confidence=0.93,
            reasoning="VPN authentication failure blocking access to internal tools.",
            model_used="test-model",
        )

    monkeypatch.setattr(main_module, "classify_ticket", fake_classify_ticket)

    payload = {
        "ticket_id": "TCK-3001",
        "subject": "Cannot login to VPN",
        "description": "Getting an authentication error since this morning.",
        "requester": "rohan.mehta@example.com",
    }

    resp = client.post("/classify", json=payload)
    assert resp.status_code == 200

    body = resp.json()
    assert body["ticket_id"] == "TCK-3001"
    assert body["subject"] == "Cannot login to VPN"
    assert body["category"] == "Network"
    assert body["subcategory"] == "VPN Access"
    assert body["priority"] == "High"
    assert 0.0 <= body["confidence"] <= 1.0
    assert body["model_used"] == "test-model"

    # A prediction log entry should have been written.
    assert log_file.exists()
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["ticket_id"] == "TCK-3001"
    assert record["output"]["category"] == "Network"


def test_classify_missing_required_field_returns_422():
    # "description" is required but missing.
    payload = {"ticket_id": "TCK-9999", "subject": "Missing description"}
    resp = client.post("/classify", json=payload)
    assert resp.status_code == 422


def test_classify_propagates_llm_failure_as_502(monkeypatch, tmp_path):
    log_file = tmp_path / "predictions.jsonl"
    monkeypatch.setattr(main_module.config, "LOG_FILE", str(log_file))

    async def failing_classify_ticket(ticket: TicketIn) -> TicketOut:
        raise RuntimeError("upstream LLM provider unreachable")

    monkeypatch.setattr(main_module, "classify_ticket", failing_classify_ticket)

    payload = {
        "ticket_id": "TCK-4000",
        "subject": "Test ticket",
        "description": "Some description",
    }

    resp = client.post("/classify", json=payload)
    assert resp.status_code == 502
    assert "Classification failed" in resp.json()["detail"]
