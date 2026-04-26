from __future__ import annotations

import pytest

from app.project_selection import ProjectCandidate, ProjectJobContext, select_projects
from app.project_selection import llm as project_llm
from app.resume_evidence.models import ProjectSkills
from app.services.project_llm_client import LLMProjectScoreResult, ProjectLLMClientError


def _candidate(
    project_id: str,
    name: str,
    *,
    technology: list[str] | None = None,
    programming: list[str] | None = None,
    concepts: list[str] | None = None,
) -> ProjectCandidate:
    return ProjectCandidate(
        id=project_id,
        name=name,
        summary=f"{name} project summary.",
        skills=ProjectSkills(
            technology=technology or [],
            programming=programming or [],
            concepts=concepts or [],
        ),
    )


def _llm_result(scores):
    return LLMProjectScoreResult(
        scores=scores,
        metadata={
            "model": "test-model",
            "api_calls": 1,
            "prompt_tokens": 20,
            "completion_tokens": 7,
            "total_tokens": 27,
            "latency_ms": 1.5,
        },
    )


def test_llm_project_selection_ranks_locally_and_preserves_metadata(monkeypatch):
    monkeypatch.setattr(
        project_llm,
        "score_projects_with_llm",
        lambda **_kwargs: _llm_result({"alpha": 2, "beta": 3, "gamma": 2}),
    )
    context = ProjectJobContext(title="Backend Engineer")
    alpha = _candidate("alpha", "Alpha")
    beta = _candidate("beta", "Beta")
    gamma = _candidate("gamma", "Gamma")

    result = select_projects(
        context=context,
        candidates=[alpha, gamma, beta],
        method="llm",
        top_n=2,
        dev_mode=True,
    )

    assert result.selected_project_ids == ["beta", "alpha"]
    assert [ranked.method for ranked in result.ranked_projects] == ["llm", "llm"]
    assert result.details["_project_llm"]["total_tokens"] == 27
    assert result.details["projects"]["beta"]["llm_score"] == 3


def test_llm_project_selection_discards_invented_ids_and_invalid_scores(monkeypatch):
    monkeypatch.setattr(
        project_llm,
        "score_projects_with_llm",
        lambda **_kwargs: _llm_result(
            {
                "good": 2,
                "bad": 4,
                "bool-score": True,
                "invented": 3,
            }
        ),
    )
    context = ProjectJobContext(title="Backend Engineer")
    good = _candidate("good", "Good")
    bad = _candidate("bad", "Bad")
    bool_score = _candidate("bool-score", "Bool")

    result = select_projects(
        context=context,
        candidates=[bad, good, bool_score],
        method="llm",
        dev_mode=True,
    )

    assert result.selected_project_ids == ["good"]
    assert "invented" not in result.selected_project_ids
    assert any("invented" in warning for warning in result.details["_warnings"])
    assert any("bad" in warning for warning in result.details["_warnings"])
    assert any("bool-score" in warning for warning in result.details["_warnings"])


def test_llm_project_selection_falls_back_to_baseline_on_client_failure(monkeypatch):
    def raise_client_error(**_kwargs):
        raise ProjectLLMClientError("network down")

    monkeypatch.setattr(project_llm, "score_projects_with_llm", raise_client_error)
    context = ProjectJobContext(title="Backend Engineer", description="Python Django API")
    project = _candidate(
        "project",
        "Project",
        technology=["Django"],
        programming=["Python"],
        concepts=["API"],
    )

    result = select_projects(
        context=context,
        candidates=[project],
        method="llm",
        dev_mode=True,
    )

    assert result.selected_project_ids == ["project"]
    assert result.ranked_projects[0].method == "baseline"
    assert result.details["_fallback_method"] == "baseline"
    assert result.details["_project_llm"]["fallback"] == "baseline"
    assert result.details["_project_llm"]["reason"].endswith("network down")


def test_llm_project_selection_falls_back_to_baseline_on_malformed_response(monkeypatch):
    monkeypatch.setattr(
        project_llm,
        "score_projects_with_llm",
        lambda **_kwargs: _llm_result(["not", "an", "object"]),
    )
    context = ProjectJobContext(title="Backend Engineer", description="Python")
    project = _candidate("project", "Project", programming=["Python"])

    result = select_projects(
        context=context,
        candidates=[project],
        method="llm",
        dev_mode=True,
    )

    assert result.selected_project_ids == ["project"]
    assert result.ranked_projects[0].method == "baseline"
    assert any("fell back to baseline" in warning for warning in result.details["_warnings"])
    assert result.details["_project_llm"]["total_tokens"] == 27


def test_project_selection_rejects_unsupported_method():
    context = ProjectJobContext(title="Backend Engineer")

    with pytest.raises(ValueError, match="Unsupported project selection method"):
        select_projects(context=context, candidates=[], method="embeddings")
