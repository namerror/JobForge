"""Integration tests for the Skill Relevance Selector API."""
import asyncio

import httpx

from app.scoring import llm as llm_scorer
from app.main import app
from app.metrics import metrics
from app.services.llm_client import LLMClientError, LLMScoreResult

PAYLOAD = {
    "job_role": "backend",
    "technology": ["Python", "Django", "PostgreSQL", "Redis", "Docker"],
    "programming": ["Python", "Java", "Go"],
    "concepts": ["API", "Microservices", "Database", "CI/CD"],
}


def api_request(method: str, path: str, **kwargs):
    async def _request():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(_request())


def test_select_skills_returns_subset():
    """Every returned skill must be present in the corresponding input list."""
    res = api_request("POST", "/select-skills", json=PAYLOAD)
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
    results = [api_request("POST", "/select-skills", json=PAYLOAD).json() for _ in range(3)]

    for category in ("technology", "programming", "concepts"):
        first = results[0][category]
        for i, result in enumerate(results[1:], start=2):
            assert result[category] == first, (
                f"Non-deterministic order in '{category}' on call {i}: "
                f"{first!r} != {result[category]!r}"
            )


def test_metrics_lite_increments():
    """Each /select-skills call must increment requests_total by exactly 1."""
    before = api_request("GET", "/metrics-lite").json()["requests_total"]
    api_request("POST", "/select-skills", json=PAYLOAD)
    after = api_request("GET", "/metrics-lite").json()["requests_total"]
    assert after == before + 1


def test_select_skills_llm_method_returns_subset(monkeypatch):
    """The LLM method must preserve the API shape and subset invariant."""
    monkeypatch.setattr(
        llm_scorer,
        "score_skills_with_llm",
        lambda **_kwargs: LLMScoreResult(
            scores={
                "technology": {"Docker": 3, "Redis": 2},
                "programming": {"Python": 3, "Go": 2},
                "concepts": {"API": 3, "Microservices": 2},
            },
            metadata={"model": "test-model", "api_calls": 1},
        ),
    )

    res = api_request(
        "POST",
        "/select-skills",
        json={**PAYLOAD, "method": "llm", "top_n": 2, "dev_mode": True},
    )

    assert res.status_code == 200
    data = res.json()
    for category in ("technology", "programming", "concepts"):
        assert set(data[category]).issubset(set(PAYLOAD[category]))
    assert data["details"]["_llm"]["model"] == "test-model"


def test_select_skills_llm_failure_falls_back_to_baseline(monkeypatch):
    """LLM scorer failures should return baseline output with a dev warning."""
    def raise_client_error(**_kwargs):
        raise LLMClientError("simulated outage")

    monkeypatch.setattr(llm_scorer, "score_skills_with_llm", raise_client_error)

    res = api_request(
        "POST",
        "/select-skills",
        json={**PAYLOAD, "method": "llm", "top_n": 2, "dev_mode": True},
    )

    assert res.status_code == 200
    data = res.json()
    assert data["details"]["_llm"]["fallback"] == "baseline"
    assert any("fell back to baseline" in warning for warning in data["details"]["_warnings"])


def test_select_skills_unsupported_method_returns_400():
    res = api_request("POST", "/select-skills", json={**PAYLOAD, "method": "not-a-method"})
    assert res.status_code == 400
