from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import pytest
import yaml
from pydantic import ValidationError

from app.main import app
from app.project_selection.llm_client import LLMProjectScoreResult
from app.skill_selection.llm_client import LLMScoreResult
from resume_generation import (
    ResumeGenerationConfig,
    ResumeGenerationError,
    build_skill_selection_payload,
    generate_project_bullet_points,
    generate_selection_context,
    load_generation_config,
    load_job_target,
)
from resume_generation.main import run_resume_generation_pipeline
from resume_evidence import load_evidence_yaml


def _write_yaml(path: Path, payload: dict) -> Path:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def _config_payload(**overrides) -> dict:
    payload = {
        "schema_version": 1,
        "app": {
            "base_url": "http://jobforge.test",
            "timeout_seconds": 5,
        },
        "skill_selection": {
            "method": "llm",
            "top_n": 3,
            "baseline_filter": True,
            "dev_mode": True,
            "llm_model": "skill-model",
            "llm_max_output_tokens": 777,
        },
        "project_selection": {
            "method": "llm",
            "top_n": 2,
            "dev_mode": True,
            "llm_model": "project-model",
            "llm_max_output_tokens": 880,
        },
        "bullet_point_generation": {
            "bullet_count_range": {"min": 2, "max": 4},
            "dev_mode": True,
            "llm_model": "bullet-model",
            "llm_max_output_tokens": 990,
            "link_scanning": False,
        },
    }
    payload.update(overrides)
    return payload


def _job_target_payload(**overrides) -> dict:
    payload = {
        "schema_version": 1,
        "title": "Backend Engineer",
        "description": "Build Python APIs with FastAPI.",
    }
    payload.update(overrides)
    return payload


def _skills_payload() -> dict:
    return {
        "schema_version": 1,
        "skills": {
            "technology": ["FastAPI", "Django"],
            "programming": ["Python"],
            "concepts": ["API"],
        },
    }


def _projects_payload() -> dict:
    return {
        "schema_version": 1,
        "projects": [
            {
                "id": "active-project",
                "name": "Active Project",
                "summary": "FastAPI backend service.",
                "highlights": ["Built the service."],
                "active": True,
                "skills": {
                    "technology": ["FastAPI"],
                    "programming": ["Python"],
                    "concepts": ["API"],
                },
                "links": ["https://example.com/active"],
            },
            {
                "id": "inactive-project",
                "name": "Inactive Project",
                "summary": "Inactive frontend project.",
                "highlights": ["Built the frontend."],
                "active": False,
                "skills": {
                    "technology": ["Angular"],
                    "programming": ["JavaScript"],
                    "concepts": ["UI"],
                },
                "links": None,
            },
        ],
    }


def _loaded_evidence(projects_path: Path, skills_path: Path) -> dict:
    return {
        "projects": load_evidence_yaml(projects_path, "projects"),
        "skills": load_evidence_yaml(skills_path, "skills"),
    }


def test_load_generation_config_returns_typed_config(tmp_path):
    path = _write_yaml(tmp_path / "config.yaml", _config_payload())

    config = load_generation_config(path)

    assert isinstance(config, ResumeGenerationConfig)
    assert config.app.base_url == "http://jobforge.test"
    assert config.skill_selection.llm_model == "skill-model"
    assert config.project_selection.llm_max_output_tokens == 880
    assert config.bullet_point_generation.llm_model == "bullet-model"
    assert config.bullet_point_generation.bullet_count_range is not None
    assert config.bullet_point_generation.bullet_count_range.min == 2


def test_load_generation_config_rejects_invalid_bullet_count_range(tmp_path):
    path = _write_yaml(
        tmp_path / "config.yaml",
        _config_payload(
            bullet_point_generation={
                "bullet_count_range": {"min": 0, "max": 4},
                "dev_mode": True,
            }
        ),
    )

    with pytest.raises(ValidationError, match="bullet_count_range.min"):
        load_generation_config(path)


def test_load_job_target_rejects_extra_fields(tmp_path):
    path = _write_yaml(tmp_path / "job.yaml", _job_target_payload(extra="nope"))

    with pytest.raises(ValidationError):
        load_job_target(path)


def test_build_skill_selection_payload_uses_evidence_and_config(tmp_path):
    config_path = _write_yaml(tmp_path / "config.yaml", _config_payload())
    job_path = _write_yaml(tmp_path / "job.yaml", _job_target_payload())
    skills_path = _write_yaml(tmp_path / "skills.yaml", _skills_payload())

    config = load_generation_config(config_path)
    job_target = load_job_target(job_path)

    skills_file = load_evidence_yaml(skills_path, "skills")

    payload = build_skill_selection_payload(
        job_target=job_target,
        skills_file=skills_file,
        config=config,
    )

    assert payload == {
        "job_role": "Backend Engineer",
        "job_text": "Build Python APIs with FastAPI.",
        "technology": ["FastAPI", "Django"],
        "programming": ["Python"],
        "concepts": ["API"],
        "method": "llm",
        "top_n": 3,
        "baseline_filter": True,
        "dev_mode": True,
        "llm_model": "skill-model",
        "llm_max_output_tokens": 777,
    }


def test_generate_selection_context_posts_evidence_payloads(monkeypatch, tmp_path):
    config_path = _write_yaml(tmp_path / "config.yaml", _config_payload())
    job_path = _write_yaml(tmp_path / "job.yaml", _job_target_payload())
    projects_path = _write_yaml(tmp_path / "projects.yaml", _projects_payload())
    skills_path = _write_yaml(tmp_path / "skills.yaml", _skills_payload())
    config = load_generation_config(config_path)
    job_target = load_job_target(job_path)
    requests: list[tuple[str, dict]] = []

    class FakeClient:
        def __init__(self, *, base_url: str, timeout: float):
            assert base_url == "http://jobforge.test"
            assert timeout == 5

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def post(self, endpoint: str, json: dict):
            requests.append((endpoint, json))
            if endpoint == "/select-skills":
                return httpx.Response(
                    200,
                    json={
                        "technology": ["FastAPI"],
                        "programming": ["Python"],
                        "concepts": ["API"],
                        "details": {"method": "llm"},
                    },
                )
            if endpoint == "/select-projects":
                return httpx.Response(
                    200,
                    json={
                        "selected_project_ids": ["active-project"],
                        "ranked_projects": [
                            {
                                "project_id": "active-project",
                                "score": 1.0,
                                "method": "llm",
                            }
                        ],
                        "details": {"method": "llm"},
                    },
                )
            raise AssertionError(f"unexpected endpoint: {endpoint}")

    monkeypatch.setattr("resume_generation.selection.httpx.Client", FakeClient)

    result = generate_selection_context(
        loaded_evidence=_loaded_evidence(projects_path, skills_path),
        config=config,
        job_target=job_target,
        config_path=config_path,
        job_target_path=job_path,
        evidence_paths={
            "projects": projects_path,
            "skills": skills_path,
        },
    )

    assert [endpoint for endpoint, _ in requests] == ["/select-skills", "/select-projects"]
    assert requests[0][1]["llm_model"] == "skill-model"
    assert requests[1][1]["llm_model"] == "project-model"
    assert [candidate["id"] for candidate in requests[1][1]["candidates"]] == ["active-project"]
    assert result.selected_skills.technology == ["FastAPI"]
    assert [project.id for project in result.selected_projects] == ["active-project"]


def test_generate_project_bullet_points_posts_once_per_selected_project(monkeypatch, tmp_path):
    config_path = _write_yaml(tmp_path / "config.yaml", _config_payload())
    job_path = _write_yaml(tmp_path / "job.yaml", _job_target_payload())
    projects_path = _write_yaml(tmp_path / "projects.yaml", _projects_payload())
    skills_path = _write_yaml(tmp_path / "skills.yaml", _skills_payload())
    config = load_generation_config(config_path)
    job_target = load_job_target(job_path)
    projects_file = _loaded_evidence(projects_path, skills_path)["projects"]
    selected_project = projects_file.projects_by_id()["active-project"]
    requests: list[tuple[str, dict]] = []

    class FakeClient:
        def __init__(self, *, base_url: str, timeout: float):
            assert base_url == "http://jobforge.test"
            assert timeout == 5

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def post(self, endpoint: str, json: dict):
            requests.append((endpoint, json))
            return httpx.Response(
                200,
                json={
                    "bullet_points": [f"Generated bullet for {json['project']['id']}."],
                    "details": {"method": "llm"},
                },
            )

    monkeypatch.setattr("resume_generation.bullet_points.httpx.Client", FakeClient)

    result = generate_project_bullet_points(
        selected_projects=[selected_project],
        config=config,
        job_target=job_target,
    )

    assert [endpoint for endpoint, _ in requests] == ["/generate-bulletpoints"]
    payload = requests[0][1]
    assert payload["context"] == {
        "title": "Backend Engineer",
        "description": "Build Python APIs with FastAPI.",
    }
    assert payload["project"]["id"] == "active-project"
    assert payload["project"]["highlights"] == ["Built the service."]
    assert payload["bullet_count_range"] == {"min": 2, "max": 4}
    assert payload["llm_model"] == "bullet-model"
    assert payload["llm_max_output_tokens"] == 990
    assert payload["link_scanning"] is False
    assert [item.project_id for item in result] == ["active-project"]
    assert result[0].bullet_points == ["Generated bullet for active-project."]


def test_generate_project_bullet_points_wraps_http_errors(monkeypatch, tmp_path):
    config_path = _write_yaml(tmp_path / "config.yaml", _config_payload())
    job_path = _write_yaml(tmp_path / "job.yaml", _job_target_payload())
    projects_path = _write_yaml(tmp_path / "projects.yaml", _projects_payload())
    skills_path = _write_yaml(tmp_path / "skills.yaml", _skills_payload())
    config = load_generation_config(config_path)
    job_target = load_job_target(job_path)
    projects_file = _loaded_evidence(projects_path, skills_path)["projects"]
    selected_project = projects_file.projects_by_id()["active-project"]

    class FailingClient:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def post(self, endpoint: str, json: dict):
            return httpx.Response(502, text="llm down")

    monkeypatch.setattr("resume_generation.bullet_points.httpx.Client", FailingClient)

    with pytest.raises(ResumeGenerationError, match="/generate-bulletpoints returned 502"):
        generate_project_bullet_points(
            selected_projects=[selected_project],
            config=config,
            job_target=job_target,
        )


def test_generate_selection_context_wraps_http_errors(monkeypatch, tmp_path):
    config_path = _write_yaml(tmp_path / "config.yaml", _config_payload())
    job_path = _write_yaml(tmp_path / "job.yaml", _job_target_payload())
    projects_path = _write_yaml(tmp_path / "projects.yaml", _projects_payload())
    skills_path = _write_yaml(tmp_path / "skills.yaml", _skills_payload())
    config = load_generation_config(config_path)
    job_target = load_job_target(job_path)

    class FailingClient:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def post(self, endpoint: str, json: dict):
            return httpx.Response(500, text="server down")

    monkeypatch.setattr("resume_generation.selection.httpx.Client", FailingClient)

    with pytest.raises(ResumeGenerationError, match="/select-skills returned 500"):
        generate_selection_context(
            loaded_evidence=_loaded_evidence(projects_path, skills_path),
            config=config,
            job_target=job_target,
            config_path=config_path,
            job_target_path=job_path,
            evidence_paths={
                "projects": projects_path,
                "skills": skills_path,
            },
        )


def test_resume_generation_pipeline_loads_config_job_and_evidence_once(monkeypatch, tmp_path):
    config_path = _write_yaml(tmp_path / "config.yaml", _config_payload())
    job_path = _write_yaml(tmp_path / "job.yaml", _job_target_payload())
    projects_path = _write_yaml(tmp_path / "projects.yaml", _projects_payload())
    skills_path = _write_yaml(tmp_path / "skills.yaml", _skills_payload())
    loaded_evidence = _loaded_evidence(projects_path, skills_path)
    calls: list[str] = []

    class FakeClient:
        def __init__(self, *, base_url: str, timeout: float):
            assert base_url == "http://jobforge.test"
            assert timeout == 5

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def post(self, endpoint: str, json: dict):
            calls.append(endpoint)
            if endpoint == "/select-skills":
                return httpx.Response(
                    200,
                    json={
                        "technology": ["FastAPI"],
                        "programming": ["Python"],
                        "concepts": ["API"],
                        "details": {"method": "llm"},
                    },
                )
            if endpoint == "/select-projects":
                return httpx.Response(
                    200,
                    json={
                        "selected_project_ids": ["active-project"],
                        "ranked_projects": [
                            {
                                "project_id": "active-project",
                                "score": 1.0,
                                "method": "llm",
                            }
                        ],
                    },
                )
            if endpoint == "/generate-bulletpoints":
                return httpx.Response(
                    200,
                    json={
                        "bullet_points": ["Generated bullet for active-project."],
                    },
                )
            raise AssertionError(f"unexpected endpoint: {endpoint}")

    monkeypatch.setattr("resume_generation.selection.httpx.Client", FakeClient)
    monkeypatch.setattr("resume_generation.bullet_points.httpx.Client", FakeClient)
    monkeypatch.setattr(
        "resume_generation.main.load_registered_evidence",
        lambda paths=None: loaded_evidence,
    )

    result = run_resume_generation_pipeline(
        config_path=config_path,
        job_target_path=job_path,
        evidence_paths={
            "projects": projects_path,
            "skills": skills_path,
        },
    )

    assert calls == ["/select-skills", "/select-projects", "/generate-bulletpoints"]
    assert [item.project_id for item in result] == ["active-project"]


def api_request(method: str, path: str, **kwargs):
    async def _request():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(_request())


def test_skill_selection_api_uses_request_llm_overrides(monkeypatch):
    captured: dict = {}

    def fake_score_skills_with_llm(**kwargs):
        captured.update(kwargs)
        return LLMScoreResult(
            scores={
                "technology": {"FastAPI": 3},
                "programming": {"Python": 3},
                "concepts": {"API": 3},
            },
            metadata={"model": kwargs["model"], "total_tokens": 0},
        )

    monkeypatch.setattr(
        "app.skill_selection.scoring.llm.score_skills_with_llm",
        fake_score_skills_with_llm,
    )

    response = api_request(
        "POST",
        "/select-skills",
        json={
            "job_role": "Backend Engineer",
            "job_text": "Build APIs.",
            "technology": ["FastAPI"],
            "programming": ["Python"],
            "concepts": ["API"],
            "method": "llm",
            "dev_mode": True,
            "llm_model": "request-skill-model",
            "llm_max_output_tokens": 333,
        },
    )

    assert response.status_code == 200
    assert captured["model"] == "request-skill-model"
    assert captured["max_output_tokens"] == 333
    assert response.json()["details"]["_llm"]["model"] == "request-skill-model"


def test_project_selection_api_uses_request_llm_overrides(monkeypatch):
    captured: dict = {}

    def fake_score_projects_with_llm(**kwargs):
        captured.update(kwargs)
        return LLMProjectScoreResult(
            scores={"jobforge": 3},
            metadata={"model": kwargs["model"], "total_tokens": 0},
        )

    monkeypatch.setattr(
        "app.project_selection.llm.score_projects_with_llm",
        fake_score_projects_with_llm,
    )

    response = api_request(
        "POST",
        "/select-projects",
        json={
            "context": {
                "title": "Backend Engineer",
                "description": "Build APIs.",
            },
            "candidates": [
                {
                    "id": "jobforge",
                    "name": "JobForge",
                    "summary": "FastAPI backend API.",
                    "skills": {
                        "technology": ["FastAPI"],
                        "programming": ["Python"],
                        "concepts": ["API"],
                    },
                }
            ],
            "method": "llm",
            "dev_mode": True,
            "llm_model": "request-project-model",
            "llm_max_output_tokens": 444,
        },
    )

    assert response.status_code == 200
    assert captured["model"] == "request-project-model"
    assert captured["max_output_tokens"] == 444
    assert response.json()["details"]["_project_llm"]["model"] == "request-project-model"
