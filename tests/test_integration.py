"""Integration tests for the Skill Relevance Selector API."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.metrics import metrics

client = TestClient(app)

PAYLOAD = {
    "job_role": "backend",
    "technology": ["Python", "Django", "PostgreSQL", "Redis", "Docker"],
    "programming": ["Python", "Java", "Go"],
    "concepts": ["API", "Microservices", "Database", "CI/CD"],
}


def test_select_skills_returns_subset():
    """Every returned skill must be present in the corresponding input list."""
    res = client.post("/select-skills", json=PAYLOAD)
    assert res.status_code == 200
    data = res.json()

    for category in ("technology", "programming", "concepts"):
        for skill in data[category]:
            assert skill in PAYLOAD[category], (
                f"Invented skill {skill!r} in '{category}' "
                f"not present in input {PAYLOAD[category]}"
            )


def test_deterministic_ordering():
    """Three identical calls must return lists in the exact same order."""
    results = [client.post("/select-skills", json=PAYLOAD).json() for _ in range(3)]

    for category in ("technology", "programming", "concepts"):
        first = results[0][category]
        for i, result in enumerate(results[1:], start=2):
            assert result[category] == first, (
                f"Non-deterministic order in '{category}' on call {i}: "
                f"{first!r} != {result[category]!r}"
            )


def test_metrics_lite_increments():
    """Each /select-skills call must increment requests_total by exactly 1."""
    before = client.get("/metrics-lite").json()["requests_total"]
    client.post("/select-skills", json=PAYLOAD)
    after = client.get("/metrics-lite").json()["requests_total"]
    assert after == before + 1
