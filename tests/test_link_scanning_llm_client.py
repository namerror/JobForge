from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

import app.link_scanning.llm_client as link_llm_client
from app.link_scanning.llm_client import (
    LinkScanningLLMClientError,
    build_link_scan_instructions,
    build_link_scan_prompt_payload,
    build_link_scan_response_create_kwargs,
    build_link_scan_schema,
    classify_link_scan_target,
    scan_project_links_with_llm,
)
from app.link_scanning.models import LinkScanJobContext
from resume_evidence.models import ProjectRecord, ProjectSkills


def _project() -> ProjectRecord:
    return ProjectRecord(
        id="jobforge",
        name="JobForge",
        summary="FastAPI resume engine for grounded resume generation.",
        highlights=["Built project and skill selection APIs."],
        active=True,
        skills=ProjectSkills(
            technology=["FastAPI"],
            programming=["Python"],
            concepts=["API"],
        ),
        links=["https://example.com/jobforge", "https://docs.example.com/jobforge"],
    )


def _github_project() -> ProjectRecord:
    return ProjectRecord(
        id="jobforge",
        name="JobForge",
        summary="FastAPI resume engine for grounded resume generation.",
        highlights=["Built project and skill selection APIs."],
        active=True,
        skills=ProjectSkills(
            technology=["FastAPI"],
            programming=["Python"],
            concepts=["API"],
        ),
        links=[
            "https://github.com/openai/jobforge",
            "https://example.com/jobforge",
        ],
    )


def test_classify_link_scan_target_detects_github_repo_roots_and_subpaths():
    root = classify_link_scan_target("https://github.com/openai/jobforge")
    blob = classify_link_scan_target(
        "https://github.com/openai/jobforge/blob/main/README.md"
    )
    tree = classify_link_scan_target("https://www.github.com/openai/jobforge/tree/main/app")

    assert root.mode == "github_repo"
    assert root.repo_scope == "https://github.com/openai/jobforge"
    assert blob.mode == "github_repo"
    assert blob.repo_scope == "https://github.com/openai/jobforge"
    assert tree.mode == "github_repo"
    assert tree.repo_scope == "https://github.com/openai/jobforge"


def test_classify_link_scan_target_keeps_non_repo_github_urls_single_page():
    owner_only = classify_link_scan_target("https://github.com/openai")
    topics = classify_link_scan_target("https://github.com/topics/python")
    gist = classify_link_scan_target("https://gist.github.com/openai/abc123")
    raw = classify_link_scan_target(
        "https://raw.githubusercontent.com/openai/jobforge/main/README.md"
    )

    assert owner_only.mode == "single_page"
    assert topics.mode == "single_page"
    assert gist.mode == "single_page"
    assert raw.mode == "single_page"


def test_build_link_scan_schema_returns_highlight_only_contract():
    schema = build_link_scan_schema()

    assert schema["required"] == ["highlights"]
    assert schema["additionalProperties"] is False
    highlight_schema = schema["properties"]["highlights"]["items"]
    assert highlight_schema["required"] == ["text", "source_url"]
    assert "skills" not in json.dumps(schema)


def test_build_link_scan_prompt_payload_includes_links_and_grounding_rules():
    payload = json.loads(
        build_link_scan_prompt_payload(
            context=LinkScanJobContext(title="Backend Engineer", description="Build APIs."),
            project=_project(),
        )
    )

    assert payload["job"]["title"] == "Backend Engineer"
    assert payload["project"]["links"] == [
        "https://example.com/jobforge",
        "https://docs.example.com/jobforge",
    ]
    assert [target["mode"] for target in payload["scan_targets"]] == [
        "single_page",
        "single_page",
    ]
    assert any("single page" in rule for rule in payload["grounding_rules"])
    assert any("Do not add skills" in rule for rule in payload["grounding_rules"])


def test_build_link_scan_prompt_payload_marks_github_repo_targets():
    payload = json.loads(
        build_link_scan_prompt_payload(
            context=LinkScanJobContext(title="Backend Engineer", description="Build APIs."),
            project=_github_project(),
        )
    )

    assert payload["scan_targets"][0] == {
        "url": "https://github.com/openai/jobforge",
        "mode": "github_repo",
        "repo_scope": "https://github.com/openai/jobforge",
        "instructions": (
            "Inspect the GitHub repository under repo_scope. You may move between "
            "repository pages such as README, source tree, docs, manifests, tests, "
            "and CI/config files, but do not leave this repository."
        ),
    }
    assert payload["scan_targets"][1]["mode"] == "single_page"
    assert any("github_repo targets" in rule for rule in payload["grounding_rules"])
    assert any("architecture" in rule for rule in payload["grounding_rules"])


def test_build_link_scan_instructions_forbids_skill_addition():
    instructions = build_link_scan_instructions()

    assert "Use web search" in instructions
    assert "do not crawl additional pages" in instructions
    assert "github_repo targets" in instructions
    assert "same repository" in instructions
    assert "Do not include skills" in instructions


def test_build_link_scan_response_create_kwargs_uses_web_search_and_strict_schema():
    kwargs = build_link_scan_response_create_kwargs(
        model="test-model",
        instructions="instructions",
        prompt_payload="{}",
        schema=build_link_scan_schema(),
        max_output_tokens=444,
    )

    assert kwargs["model"] == "test-model"
    assert kwargs["tools"] == [{"type": "web_search"}]
    assert kwargs["tool_choice"] == "required"
    assert kwargs["include"] == ["web_search_call.action.sources"]
    assert kwargs["temperature"] == 0
    assert kwargs["text"]["format"]["name"] == "project_link_scan"
    assert kwargs["text"]["format"]["strict"] is True


def test_scan_project_links_with_llm_sends_web_search_request(monkeypatch):
    captured = {}

    class DummyResponses:
        def create(self, **kwargs):
            captured["kwargs"] = kwargs
            return SimpleNamespace(
                output_text=json.dumps(
                    {
                        "highlights": [
                            {
                                "text": "Scanned README confirms grounded resume orchestration.",
                                "source_url": "https://example.com/jobforge",
                            }
                        ]
                    }
                ),
                output=[
                    SimpleNamespace(
                        action=SimpleNamespace(
                            sources=[SimpleNamespace(url="https://example.com/jobforge")]
                        )
                    )
                ],
                usage=SimpleNamespace(input_tokens=20, output_tokens=10, total_tokens=30),
            )

    class DummyOpenAI:
        def __init__(self, **kwargs):
            captured["init"] = kwargs
            self.responses = DummyResponses()

    monkeypatch.setattr(link_llm_client, "OpenAI", DummyOpenAI)
    monkeypatch.setattr(link_llm_client.settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(link_llm_client.settings, "LINK_SCANNING_LLM_MODEL", "test-model")
    monkeypatch.setattr(link_llm_client.settings, "LINK_SCANNING_LLM_MAX_OUTPUT_TOKENS", 555)

    result = scan_project_links_with_llm(
        context=LinkScanJobContext(title="Backend Engineer"),
        project=_project(),
    )

    assert captured["init"]["api_key"] == "test-key"
    kwargs = captured["kwargs"]
    assert kwargs["model"] == "test-model"
    assert kwargs["max_output_tokens"] == 555
    assert kwargs["tools"] == [{"type": "web_search"}]
    assert kwargs["tool_choice"] == "required"
    payload = json.loads(kwargs["input"])
    assert payload["project"]["id"] == "jobforge"
    assert len(payload["project"]["links"]) == 2
    assert result.highlights[0].text.startswith("Scanned README")
    assert result.metadata["source_urls"] == ["https://example.com/jobforge"]
    assert result.metadata["total_tokens"] == 30


def test_scan_project_links_with_llm_accepts_same_github_repo_source(monkeypatch):
    class DummyResponses:
        def create(self, **_kwargs):
            return SimpleNamespace(
                output_text=json.dumps(
                    {
                        "highlights": [
                            {
                                "text": "README and tests show a FastAPI orchestration layer with deterministic evidence validation.",
                                "source_url": "https://github.com/openai/jobforge/blob/main/README.md",
                            }
                        ]
                    }
                ),
                output=[
                    SimpleNamespace(
                        action=SimpleNamespace(
                            sources=[
                                SimpleNamespace(
                                    url="https://github.com/openai/other-repo/blob/main/README.md"
                                )
                            ]
                        )
                    )
                ],
                usage=None,
            )

    class DummyOpenAI:
        def __init__(self, **_kwargs):
            self.responses = DummyResponses()

    monkeypatch.setattr(link_llm_client, "OpenAI", DummyOpenAI)
    monkeypatch.setattr(link_llm_client.settings, "OPENAI_API_KEY", "test-key")

    result = scan_project_links_with_llm(
        context=LinkScanJobContext(title="Backend Engineer"),
        project=_github_project(),
    )

    assert result.highlights[0].source_url == (
        "https://github.com/openai/jobforge/blob/main/README.md"
    )
    assert result.metadata["scan_targets"][0]["mode"] == "github_repo"
    assert result.metadata["scan_targets"][0]["repo_scope"] == (
        "https://github.com/openai/jobforge"
    )


def test_scan_project_links_with_llm_omits_temperature_for_gpt_5_mini(monkeypatch):
    captured = {}

    class DummyResponses:
        def create(self, **kwargs):
            captured["kwargs"] = kwargs
            return SimpleNamespace(
                output_text='{"highlights":[]}',
                output=[],
                usage=None,
            )

    class DummyOpenAI:
        def __init__(self, **_kwargs):
            self.responses = DummyResponses()

    monkeypatch.setattr(link_llm_client, "OpenAI", DummyOpenAI)
    monkeypatch.setattr(link_llm_client.settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(link_llm_client.settings, "LINK_SCANNING_LLM_MODEL", "gpt-5-mini")

    scan_project_links_with_llm(
        context=LinkScanJobContext(title="Backend Engineer"),
        project=_project(),
    )

    assert "temperature" not in captured["kwargs"]


def test_scan_project_links_with_llm_rejects_invalid_json(monkeypatch):
    class DummyResponses:
        def create(self, **_kwargs):
            return SimpleNamespace(output_text="{not-json", output=[], usage=None)

    class DummyOpenAI:
        def __init__(self, **_kwargs):
            self.responses = DummyResponses()

    monkeypatch.setattr(link_llm_client, "OpenAI", DummyOpenAI)
    monkeypatch.setattr(link_llm_client.settings, "OPENAI_API_KEY", "test-key")

    with pytest.raises(LinkScanningLLMClientError, match="valid JSON"):
        scan_project_links_with_llm(
            context=LinkScanJobContext(title="Backend Engineer"),
            project=_project(),
        )


def test_scan_project_links_with_llm_rejects_unknown_source_url(monkeypatch):
    class DummyResponses:
        def create(self, **_kwargs):
            return SimpleNamespace(
                output_text=json.dumps(
                    {
                        "highlights": [
                            {
                                "text": "Unsupported source.",
                                "source_url": "https://unrelated.example.com/page",
                            }
                        ]
                    }
                ),
                output=[
                    SimpleNamespace(
                        action=SimpleNamespace(
                            sources=[
                                SimpleNamespace(
                                    url="https://github.com/openai/other-repo/blob/main/README.md"
                                )
                            ]
                        )
                    )
                ],
                usage=None,
            )

    class DummyOpenAI:
        def __init__(self, **_kwargs):
            self.responses = DummyResponses()

    monkeypatch.setattr(link_llm_client, "OpenAI", DummyOpenAI)
    monkeypatch.setattr(link_llm_client.settings, "OPENAI_API_KEY", "test-key")

    with pytest.raises(LinkScanningLLMClientError, match="source_url"):
        scan_project_links_with_llm(
            context=LinkScanJobContext(title="Backend Engineer"),
            project=_project(),
        )


def test_scan_project_links_with_llm_rejects_other_github_repo_source(monkeypatch):
    class DummyResponses:
        def create(self, **_kwargs):
            return SimpleNamespace(
                output_text=json.dumps(
                    {
                        "highlights": [
                            {
                                "text": "Unsupported cross-repo source.",
                                "source_url": "https://github.com/openai/other-repo/blob/main/README.md",
                            }
                        ]
                    }
                ),
                output=[
                    SimpleNamespace(
                        action=SimpleNamespace(
                            sources=[
                                SimpleNamespace(
                                    url="https://github.com/openai/other-repo/blob/main/README.md"
                                )
                            ]
                        )
                    )
                ],
                usage=None,
            )

    class DummyOpenAI:
        def __init__(self, **_kwargs):
            self.responses = DummyResponses()

    monkeypatch.setattr(link_llm_client, "OpenAI", DummyOpenAI)
    monkeypatch.setattr(link_llm_client.settings, "OPENAI_API_KEY", "test-key")

    with pytest.raises(LinkScanningLLMClientError, match="source_url"):
        scan_project_links_with_llm(
            context=LinkScanJobContext(title="Backend Engineer"),
            project=_github_project(),
        )


def test_scan_project_links_with_llm_requires_api_key(monkeypatch):
    monkeypatch.setattr(link_llm_client.settings, "OPENAI_API_KEY", "")

    with pytest.raises(LinkScanningLLMClientError, match="OPENAI_API_KEY"):
        scan_project_links_with_llm(
            context=LinkScanJobContext(title="Backend Engineer"),
            project=_project(),
        )
