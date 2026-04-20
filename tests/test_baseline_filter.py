import asyncio

import httpx

from app.main import app
from app.metrics import metrics
from app.models import SkillSelectRequest
from app.scoring import llm as llm_scorer
from app.scoring.baseline import baseline_select_skills
from app.services import baseline_filter
from app.services import skill_selector
from app.services.llm_client import LLMScoreResult
from scripts import eval as eval_script


def api_request(method: str, path: str, **kwargs):
    async def _request():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(_request())


def _request(**overrides) -> SkillSelectRequest:
    payload = {
        "job_role": "Backend Engineer",
        "technology": ["Django", "AlphaDB"],
        "programming": ["Python", "Rustish"],
        "concepts": ["API", "Odd Concept"],
        "method": "embeddings",
        "baseline_filter": True,
        "dev_mode": True,
    }
    payload.update(overrides)
    return SkillSelectRequest(**payload)


def test_baseline_filter_false_preserves_selected_method_behavior(monkeypatch):
    calls = []

    def fake_embedding_select_skills(**kwargs):
        calls.append(kwargs)
        return (
            {
                "technology": ["AlphaDB", "Django"],
                "programming": ["Rustish"],
                "concepts": ["Odd Concept"],
            },
            {"technology": {}, "programming": {}, "concepts": {}},
        )

    monkeypatch.setattr(skill_selector, "embedding_select_skills", fake_embedding_select_skills)

    response = skill_selector.select_skills_service(
        _request(baseline_filter=False, technology=["Django", "AlphaDB"])
    )

    assert response.technology == ["AlphaDB", "Django"]
    assert calls[0]["technology"] == ["Django", "AlphaDB"]
    assert calls[0]["top_n"] == 10


def test_baseline_method_treats_baseline_filter_as_noop():
    req = _request(method="baseline", baseline_filter=True, top_n=2)
    response = skill_selector.select_skills_service(req)
    expected, _ = baseline_select_skills(
        job_role=req.job_role,
        technology=req.technology,
        programming=req.programming,
        concepts=req.concepts,
        job_text=req.job_text,
        top_n=2,
        dev_mode=True,
    )

    assert response.technology == expected["technology"]
    assert response.programming == expected["programming"]
    assert response.concepts == expected["concepts"]


def test_baseline_filter_sends_only_unrecognized_skills_to_second_pass(monkeypatch):
    calls = []

    def fake_embedding_select_skills(**kwargs):
        calls.append(kwargs)
        return (
            {
                "technology": ["AlphaDB"],
                "programming": ["Rustish"],
                "concepts": ["Odd Concept"],
            },
            {
                "technology": {"AlphaDB": {"similarity": 0.8, "normalized_skill": "alphadb"}},
                "programming": {"Rustish": {"similarity": 0.7, "normalized_skill": "rustish"}},
                "concepts": {"Odd Concept": {"similarity": 0.6, "normalized_skill": "odd concept"}},
            },
        )

    monkeypatch.setattr(baseline_filter, "embedding_select_skills", fake_embedding_select_skills)

    response = skill_selector.select_skills_service(_request())

    assert calls[0]["technology"] == ["AlphaDB"]
    assert calls[0]["programming"] == ["Rustish"]
    assert calls[0]["concepts"] == ["Odd Concept"]
    assert set(response.technology).issubset({"Django", "AlphaDB"})
    assert response.details["_baseline_filter"]["categories"]["technology"] == {
        "recognized": 1,
        "unrecognized": 1,
        "second_pass_scored": 1,
    }
    assert response.details["technology"]["Django"]["source"] == "baseline"
    assert response.details["technology"]["AlphaDB"]["source"] == "embeddings"


def test_baseline_filter_keeps_normalized_profile_aliases_in_baseline(monkeypatch):
    calls = []

    def fake_embedding_select_skills(**kwargs):
        calls.append(kwargs)
        return (
            {"technology": ["AlphaDB"], "programming": [], "concepts": []},
            {
                "technology": {"AlphaDB": {"similarity": 0.8, "normalized_skill": "alphadb"}},
                "programming": {},
                "concepts": {},
            },
        )

    monkeypatch.setattr(baseline_filter, "embedding_select_skills", fake_embedding_select_skills)
    req = _request(
        technology=["AWS", "Node.JS", "AlphaDB"],
        programming=[],
        concepts=[],
        top_n=3,
    )

    response = skill_selector.select_skills_service(req)

    assert calls[0]["technology"] == ["AlphaDB"]
    assert calls[0]["programming"] == []
    assert calls[0]["concepts"] == []
    assert response.details["_baseline_filter"]["categories"]["technology"] == {
        "recognized": 2,
        "unrecognized": 1,
        "second_pass_scored": 1,
    }
    assert response.details["technology"]["AWS"]["source"] == "baseline"
    assert response.details["technology"]["AWS"]["normalized_skill"] == "amazon web services"
    assert response.details["technology"]["Node.JS"]["source"] == "baseline"
    assert response.details["technology"]["Node.JS"]["normalized_skill"] == "nodejs"
    assert response.details["technology"]["AlphaDB"]["source"] == "embeddings"


def test_baseline_filter_keeps_token_containment_matches_in_baseline(monkeypatch):
    calls = []

    def fake_embedding_select_skills(**kwargs):
        calls.append(kwargs)
        return (
            {"technology": [], "programming": [], "concepts": ["Odd Concept"]},
            {
                "technology": {},
                "programming": {},
                "concepts": {"Odd Concept": {"similarity": 0.7, "normalized_skill": "odd concept"}},
            },
        )

    monkeypatch.setattr(baseline_filter, "embedding_select_skills", fake_embedding_select_skills)
    req = _request(
        technology=[],
        programming=[],
        concepts=["Database Management", "Odd Concept"],
        top_n=2,
    )

    response = skill_selector.select_skills_service(req)

    assert calls[0]["technology"] == []
    assert calls[0]["programming"] == []
    assert calls[0]["concepts"] == ["Odd Concept"]
    assert response.details["_baseline_filter"]["categories"]["concepts"] == {
        "recognized": 1,
        "unrecognized": 1,
        "second_pass_scored": 1,
    }
    assert response.details["concepts"]["Database Management"]["source"] == "baseline"
    assert response.details["concepts"]["Database Management"]["baseline_score"] == 3.0
    assert response.details["concepts"]["Odd Concept"]["source"] == "embeddings"


def test_baseline_filter_final_ranking_is_deterministic_after_merge(monkeypatch):
    def fake_embedding_select_skills(**_kwargs):
        return (
            {"technology": ["Zeta", "Alpha"], "programming": [], "concepts": []},
            {
                "technology": {
                    "Zeta": {"similarity": 1.0, "normalized_skill": "zeta"},
                    "Alpha": {"similarity": 1.0, "normalized_skill": "alpha"},
                },
                "programming": {},
                "concepts": {},
            },
        )

    monkeypatch.setattr(baseline_filter, "embedding_select_skills", fake_embedding_select_skills)
    req = _request(
        technology=["Django", "Zeta", "Alpha"],
        programming=[],
        concepts=[],
        top_n=3,
    )

    results = [skill_selector.select_skills_service(req).technology for _ in range(3)]

    assert results == [["Alpha", "Django", "Zeta"]] * 3


def test_baseline_filter_skips_second_pass_when_all_skills_are_recognized(monkeypatch):
    def fail_if_called(**_kwargs):
        raise AssertionError("second pass should not run")

    monkeypatch.setattr(baseline_filter, "embedding_select_skills", fail_if_called)
    req = _request(
        technology=["Django"],
        programming=["Python"],
        concepts=["API"],
        top_n=2,
    )

    response = skill_selector.select_skills_service(req)

    assert response.technology == ["Django"]
    assert response.programming == ["Python"]
    assert response.concepts == ["API"]
    assert response.details["_baseline_filter"]["categories"]["technology"]["unrecognized"] == 0


def test_baseline_filter_embedding_failure_returns_full_baseline(monkeypatch):
    def raise_embedding_error(**_kwargs):
        raise RuntimeError("simulated embedding outage")

    monkeypatch.setattr(baseline_filter, "embedding_select_skills", raise_embedding_error)
    req = _request(top_n=2)

    response = skill_selector.select_skills_service(req)
    expected, _ = baseline_select_skills(
        job_role=req.job_role,
        technology=req.technology,
        programming=req.programming,
        concepts=req.concepts,
        job_text=req.job_text,
        top_n=2,
        dev_mode=True,
    )

    assert response.technology == expected["technology"]
    assert response.details["_fallback_method"] == "baseline"
    assert response.details["_baseline_filter"]["fallback"] == "baseline"
    assert any("fell back to baseline" in warning for warning in response.details["_warnings"])


def test_baseline_filter_llm_fallback_metadata_returns_full_baseline_and_tokens(monkeypatch):
    def fake_llm_select_skills(**_kwargs):
        return (
            {"technology": ["AlphaDB"], "programming": [], "concepts": []},
            {
                "_fallback_method": "baseline",
                "_llm": {"fallback": "baseline", "total_tokens": 17},
                "_warnings": ["second pass fallback"],
            },
        )

    monkeypatch.setattr(baseline_filter, "llm_select_skills", fake_llm_select_skills)
    req = _request(method="llm", top_n=2)

    response = skill_selector.select_skills_service(req)

    assert response.details["_fallback_method"] == "baseline"
    assert response.details["_llm"]["total_tokens"] == 17
    assert "second pass fallback" in response.details["_warnings"]


def test_select_skills_accepts_baseline_filter_and_keeps_default_shape(monkeypatch):
    def fake_embedding_select_skills(**_kwargs):
        return (
            {"technology": ["AlphaDB"], "programming": [], "concepts": []},
            {
                "technology": {"AlphaDB": {"similarity": 0.8, "normalized_skill": "alphadb"}},
                "programming": {},
                "concepts": {},
            },
        )

    monkeypatch.setattr(baseline_filter, "embedding_select_skills", fake_embedding_select_skills)
    response = api_request(
        "POST",
        "/select-skills",
        json={
            "job_role": "Backend Engineer",
            "technology": ["Django", "AlphaDB"],
            "programming": [],
            "concepts": [],
            "method": "embeddings",
            "baseline_filter": True,
            "dev_mode": False,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"technology", "programming", "concepts", "details"}
    assert data["details"] is None
    assert set(data["technology"]).issubset({"Django", "AlphaDB"})


def test_health_includes_baseline_filter():
    response = api_request("GET", "/health")

    assert response.status_code == 200
    assert "baseline_filter" in response.json()


def test_baseline_filter_fallback_counts_baseline_usage(monkeypatch):
    def raise_embedding_error(**_kwargs):
        raise RuntimeError("simulated embedding outage")

    monkeypatch.setattr(baseline_filter, "embedding_select_skills", raise_embedding_error)
    before = api_request("GET", "/metrics-lite").json()

    response = api_request(
        "POST",
        "/select-skills",
        json={
            "job_role": "Backend Engineer",
            "technology": ["Django", "AlphaDB"],
            "programming": [],
            "concepts": [],
            "method": "embeddings",
            "baseline_filter": True,
            "dev_mode": False,
        },
    )

    assert response.status_code == 200
    after = api_request("GET", "/metrics-lite").json()
    assert after["requests_total"] == before["requests_total"] + 1
    assert after["method_usage"].get("baseline", 0) == before["method_usage"].get("baseline", 0) + 1
    assert after["method_usage"].get("embeddings", 0) == before["method_usage"].get("embeddings", 0)


def test_baseline_filter_llm_success_increments_total_tokens(monkeypatch):
    monkeypatch.setattr(
        llm_scorer,
        "score_skills_with_llm",
        lambda **_kwargs: LLMScoreResult(
            scores={
                "technology": {"AlphaDB": 3},
                "programming": {},
                "concepts": {},
            },
            metadata={
                "model": "test-model",
                "api_calls": 1,
                "prompt_tokens": 11,
                "completion_tokens": 7,
                "total_tokens": 18,
            },
        ),
    )
    before_total_tokens = metrics.total_tokens

    response = api_request(
        "POST",
        "/select-skills",
        json={
            "job_role": "Backend Engineer",
            "technology": ["Django", "AlphaDB"],
            "programming": [],
            "concepts": [],
            "method": "llm",
            "baseline_filter": True,
            "dev_mode": False,
        },
    )

    assert response.status_code == 200
    assert metrics.total_tokens == before_total_tokens + 18


def test_eval_includes_and_passes_baseline_filter_override(monkeypatch):
    seen = []

    def fake_select_skills(**kwargs):
        seen.append(kwargs["baseline_filter"])
        return (
            {"technology": ["Django"], "programming": [], "concepts": []},
            {"_llm": {"total_tokens": 0}},
        )

    monkeypatch.setattr(eval_script, "select_skills", fake_select_skills)
    result = eval_script.evaluate(
        [
            {
                "input": {
                    "job_role": "Backend Engineer",
                    "technology": ["Django"],
                    "programming": [],
                    "concepts": [],
                },
                "expected": {
                    "technology": ["Django"],
                    "programming": [],
                    "concepts": [],
                },
            }
        ],
        baseline_filter=True,
    )

    assert seen == [True]
    assert result["baseline_filter"] is True
