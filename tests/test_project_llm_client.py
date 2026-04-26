from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from app.project_selection import ProjectCandidate, ProjectJobContext
from app.resume_evidence.models import ProjectSkills
from app.services import project_llm_client
from app.services.project_llm_client import ProjectLLMClientError, score_projects_with_llm


def _candidate(project_id: str, name: str) -> ProjectCandidate:
    return ProjectCandidate(
        id=project_id,
        name=name,
        summary=f"{name} summary",
        skills=ProjectSkills(
            technology=["Django"],
            programming=["Python"],
            concepts=["API"],
        ),
    )


def test_score_projects_with_llm_sends_strict_project_schema(monkeypatch):
    captured = {}

    class DummyResponses:
        def create(self, **kwargs):
            captured["kwargs"] = kwargs
            return SimpleNamespace(
                output_text='{"jobforge":3,"portfolio":1}',
                usage=SimpleNamespace(input_tokens=12, output_tokens=5, total_tokens=17),
            )

    class DummyOpenAI:
        def __init__(self, **kwargs):
            captured["init"] = kwargs
            self.responses = DummyResponses()

    monkeypatch.setattr(project_llm_client, "OpenAI", DummyOpenAI)
    monkeypatch.setattr(project_llm_client.settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(project_llm_client.settings, "LLM_MODEL", "test-model")
    monkeypatch.setattr(project_llm_client.settings, "LLM_MAX_OUTPUT_TOKENS", 333)

    result = score_projects_with_llm(
        context=ProjectJobContext(title="Backend Engineer", description="Build APIs."),
        candidates=[_candidate("jobforge", "JobForge"), _candidate("portfolio", "Portfolio")],
    )

    assert captured["init"]["api_key"] == "test-key"
    kwargs = captured["kwargs"]
    assert kwargs["model"] == "test-model"
    assert kwargs["temperature"] == 0
    assert kwargs["max_output_tokens"] == 333
    assert kwargs["text"]["format"]["name"] == "project_scores"
    assert kwargs["text"]["format"]["strict"] is True
    schema = kwargs["text"]["format"]["schema"]
    assert schema["required"] == ["jobforge", "portfolio"]
    assert schema["properties"]["jobforge"]["minimum"] == 0
    assert schema["properties"]["jobforge"]["maximum"] == 3
    payload = json.loads(kwargs["input"])
    assert payload["job"]["title"] == "Backend Engineer"
    assert payload["projects"][0]["id"] == "jobforge"
    assert payload["projects"][0]["skills"]["programming"] == ["Python"]
    assert result.scores == {"jobforge": 3, "portfolio": 1}
    assert result.metadata["total_tokens"] == 17


def test_score_projects_with_llm_omits_temperature_for_gpt_5_mini(monkeypatch):
    captured = {}

    class DummyResponses:
        def create(self, **kwargs):
            captured["kwargs"] = kwargs
            return SimpleNamespace(output_text='{"jobforge":3}', usage=None)

    class DummyOpenAI:
        def __init__(self, **_kwargs):
            self.responses = DummyResponses()

    monkeypatch.setattr(project_llm_client, "OpenAI", DummyOpenAI)
    monkeypatch.setattr(project_llm_client.settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(project_llm_client.settings, "LLM_MODEL", "gpt-5-mini")

    score_projects_with_llm(
        context=ProjectJobContext(title="Backend Engineer"),
        candidates=[_candidate("jobforge", "JobForge")],
    )

    assert "temperature" not in captured["kwargs"]


def test_score_projects_with_llm_rejects_invalid_json(monkeypatch):
    class DummyResponses:
        def create(self, **_kwargs):
            return SimpleNamespace(output_text="{not-json", usage=None)

    class DummyOpenAI:
        def __init__(self, **_kwargs):
            self.responses = DummyResponses()

    monkeypatch.setattr(project_llm_client, "OpenAI", DummyOpenAI)
    monkeypatch.setattr(project_llm_client.settings, "OPENAI_API_KEY", "test-key")

    with pytest.raises(ProjectLLMClientError, match="valid JSON"):
        score_projects_with_llm(
            context=ProjectJobContext(title="Backend Engineer"),
            candidates=[_candidate("jobforge", "JobForge")],
        )


def test_score_projects_with_llm_requires_api_key(monkeypatch):
    monkeypatch.setattr(project_llm_client.settings, "OPENAI_API_KEY", "")

    with pytest.raises(ProjectLLMClientError, match="OPENAI_API_KEY"):
        score_projects_with_llm(
            context=ProjectJobContext(title="Backend Engineer"),
            candidates=[_candidate("jobforge", "JobForge")],
        )
