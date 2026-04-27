from types import SimpleNamespace

import pytest

from app.skill_selection import llm_client
from app.skill_selection.llm_client import LLMClientError, score_skills_with_llm


def test_score_skills_with_llm_sends_responses_schema(monkeypatch):
    captured = {}

    class DummyResponses:
        def create(self, **kwargs):
            captured["kwargs"] = kwargs
            return SimpleNamespace(
                output_text='{"technology":{"React":3},"programming":{},"concepts":{}}',
                usage=SimpleNamespace(input_tokens=12, output_tokens=8, total_tokens=20),
            )

    class DummyOpenAI:
        def __init__(self, **kwargs):
            captured["init"] = kwargs
            self.responses = DummyResponses()

    monkeypatch.setattr(llm_client, "OpenAI", DummyOpenAI)
    monkeypatch.setattr(llm_client.settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(llm_client.settings, "LLM_MODEL", "test-model")
    monkeypatch.setattr(llm_client.settings, "LLM_MAX_OUTPUT_TOKENS", 321)

    result = score_skills_with_llm(
        job_role="Frontend Engineer",
        job_text=None,
        technology=["React"],
        programming=[],
        concepts=[],
    )

    assert captured["init"]["api_key"] == "test-key"
    kwargs = captured["kwargs"]
    assert kwargs["model"] == "test-model"
    assert kwargs["temperature"] == 0
    assert kwargs["max_output_tokens"] == 321
    assert kwargs["tools"] == []
    assert kwargs["text"]["format"]["type"] == "json_schema"
    assert kwargs["text"]["format"]["strict"] is True
    schema = kwargs["text"]["format"]["schema"]
    assert schema["required"] == ["technology", "programming", "concepts"]
    assert schema["properties"]["technology"]["required"] == ["React"]
    assert result.scores["technology"]["React"] == 3
    assert result.metadata["prompt_tokens"] == 12
    assert result.metadata["completion_tokens"] == 8
    assert result.metadata["total_tokens"] == 20
    assert result.metadata["api_calls"] == 1


def test_score_skills_with_llm_omits_temperature_for_gpt_5_mini(monkeypatch):
    captured = {}

    class DummyResponses:
        def create(self, **kwargs):
            captured["kwargs"] = kwargs
            return SimpleNamespace(
                output_text='{"technology":{"React":3},"programming":{},"concepts":{}}',
                usage=SimpleNamespace(input_tokens=1, output_tokens=1, total_tokens=2),
            )

    class DummyOpenAI:
        def __init__(self, **_kwargs):
            self.responses = DummyResponses()

    monkeypatch.setattr(llm_client, "OpenAI", DummyOpenAI)
    monkeypatch.setattr(llm_client.settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(llm_client.settings, "LLM_MODEL", "gpt-5-mini")

    score_skills_with_llm(
        job_role="Frontend Engineer",
        job_text=None,
        technology=["React"],
        programming=[],
        concepts=[],
    )

    assert "temperature" not in captured["kwargs"]


def test_score_skills_with_llm_rejects_invalid_json(monkeypatch):
    class DummyResponses:
        def create(self, **_kwargs):
            return SimpleNamespace(output_text="{not-json", usage=None)

    class DummyOpenAI:
        def __init__(self, **_kwargs):
            self.responses = DummyResponses()

    monkeypatch.setattr(llm_client, "OpenAI", DummyOpenAI)
    monkeypatch.setattr(llm_client.settings, "OPENAI_API_KEY", "test-key")

    with pytest.raises(LLMClientError, match="valid JSON"):
        score_skills_with_llm(
            job_role="Backend Engineer",
            job_text=None,
            technology=[],
            programming=[],
            concepts=[],
        )


def test_score_skills_with_llm_requires_api_key(monkeypatch):
    monkeypatch.setattr(llm_client.settings, "OPENAI_API_KEY", "")

    with pytest.raises(LLMClientError, match="OPENAI_API_KEY"):
        score_skills_with_llm(
            job_role="Backend Engineer",
            job_text=None,
            technology=[],
            programming=[],
            concepts=[],
        )


def test_score_skills_with_llm_wraps_openai_errors(monkeypatch):
    class DummyResponses:
        def create(self, **_kwargs):
            raise TimeoutError("network timeout")

    class DummyOpenAI:
        def __init__(self, **_kwargs):
            self.responses = DummyResponses()

    monkeypatch.setattr(llm_client, "OpenAI", DummyOpenAI)
    monkeypatch.setattr(llm_client.settings, "OPENAI_API_KEY", "test-key")

    with pytest.raises(LLMClientError, match="LLM request failed"):
        score_skills_with_llm(
            job_role="Backend Engineer",
            job_text=None,
            technology=[],
            programming=[],
            concepts=[],
        )
