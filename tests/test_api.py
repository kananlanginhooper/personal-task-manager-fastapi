from __future__ import annotations

import os
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["API_TOKEN"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_task_lifecycle_logs_every_change(client):
    t = client.post("/api/tasks", json={"title": "Water the plants", "date": "2030-01-07", "start": "18:00", "est": 15}).json()
    assert t["origEst"] == 15

    moved = client.post(f"/api/tasks/{t['id']}/move", json={"date": "2030-01-08", "start": "19:00", "reason": "busy"}).json()
    assert moved["date"] == "2030-01-08" and len(moved["moves"]) == 1

    est = client.post(f"/api/tasks/{t['id']}/estimate", json={"est": 25, "reason": "took longer"}).json()
    assert est["est"] == 25 and est["origEst"] == 15
    assert est["estHistory"][0]["from"] == 15

    done = client.post(f"/api/tasks/{t['id']}/done", json={"done": True}).json()
    assert done["done"] and done["doneAt"]

    types = [c["type"] for c in client.get("/api/changes").json()]
    assert types[:4] == ["done", "estimate", "move", "add"]
    estimate = next(c for c in client.get("/api/changes").json() if c["type"] == "estimate")
    assert estimate["from"] == {"est": 15} and estimate["reason"] == "took longer"


def test_split_keeps_original_estimate(client):
    t = client.post("/api/tasks", json={"title": "Sort the garage", "date": "2030-01-09", "est": 60}).json()
    first, second = client.post(f"/api/tasks/{t['id']}/split", json={"reason": "too big"}).json()
    assert first["est"] + second["est"] == 60
    assert first["origEst"] == second["origEst"] == 60
    assert second["date"] == "2030-01-10" and second["splitFrom"] == t["id"]


def test_habits_and_notes(client):
    r = client.put("/api/habits/2030-01-07", json={"habit": "walk", "done": True}).json()
    assert r["marks"] == {"walk": True}
    client.put("/api/habits/2030-01-07", json={"habit": "read", "done": True})
    boot = client.get("/api/bootstrap").json()
    assert boot["habitDays"]["2030-01-07"] == {"walk": True, "read": True}

    note = client.post("/api/notes", json={"text": "Mornings work better for chores"}).json()
    assert note["status"] == "new"
    replied = client.patch(f"/api/notes/{note['id']}", json={"status": "read", "reply": "Moved chores to mornings"}).json()
    assert replied["status"] == "read" and replied["repliedAt"]


def test_award_is_idempotent(client):
    a = client.post("/api/trophies/awards", json={"id": "first", "name": "First Step"}).json()
    b = client.post("/api/trophies/awards", json={"id": "first", "name": "First Step"}).json()
    assert a["earnedAt"] == b["earnedAt"]


def test_token_required_when_configured(client, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "API_TOKEN", "secret")
    assert client.get("/api/health").status_code == 401
    assert client.get("/api/health", headers={"Authorization": "Bearer secret"}).status_code == 200
