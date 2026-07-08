from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

import httpx
import pytest
import yaml
from pydantic import ValidationError

from app.bulletpoints_generation.models import BulletGenerationResponse
from app.main import app
from app.project_selection.llm_client import LLMProjectScoreResult
from app.skill_selection.llm_client import LLMScoreResult
from resume_generation import (
    DEFAULT_RESUME_TEX_ARTIFACT_PATH,
    ExperienceBulletPointResult,
    IntermediateResumeResult,
    ProjectBulletPointResult,
    ProjectSelectionResult,
    ResumeGenerationConfig,
    ResumeGenerationError,
    ResumeSelectionContext,
    SkillSelectionResult,
    assemble_intermediate_resume_result,
    build_skill_selection_payload,
    generate_experience_bullet_points,
    generate_project_bullet_points,
    enrich_projects_with_link_scanning,
    generate_selection_context,
    latex_escape,
    load_generation_config,
    load_job_target,
    render_resume_latex,
    resolve_resume_latex_output_path,
    write_resume_latex_artifact,
)
from resume_generation.cache import ResumeGenerationStageCache
from resume_generation.main import (
    run_resume_generation_pipeline,
    write_resume_latex_from_config,
    write_resume_result_artifact,
)
from resume_generation.token_usage import extract_response_token_usage
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
        "link_scanning": {
            "enabled": False,
            "dev_mode": True,
            "llm_model": "link-model",
            "llm_max_output_tokens": 660,
        },
        "project_bullet_point_generation": {
            "bullet_count_range": {"min": 2, "max": 4},
            "dev_mode": True,
            "llm_model": "project-bullet-model",
            "llm_max_output_tokens": 990,
        },
        "experience_bullet_point_generation": {
            "bullet_count_range": {"min": 1, "max": 2},
            "dev_mode": True,
            "llm_model": "experience-bullet-model",
            "llm_max_output_tokens": 990,
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


def _user_payload() -> dict:
    return {
        "schema_version": 1,
        "name": "Example Candidate",
        "email": "candidate@example.com",
        "phone": "+1 555-0100",
        "linkedin": "https://www.linkedin.com/in/example-candidate",
        "github": "https://github.com/example-candidate",
    }


def _education_payload() -> dict:
    return {
        "schema_version": 1,
        "education": [
            {
                "name": "Example University",
                "degree": "Bachelor of Science in Computer Science",
                "grade": "3.8 GPA",
                "start": "2020",
                "end": "2024",
                "location": "Example City, ST",
                "relevant_coursework": ["Data Structures", "Algorithms"],
            }
        ],
    }


def _experience_payload() -> dict:
    return {
        "schema_version": 1,
        "experience": [
            {
                "id": "backend-engineer",
                "name": "Example Company",
                "role": "Backend Engineer",
                "summary": "Built backend services for internal platforms.",
                "highlights": ["Designed schema-validated APIs."],
                "active": True,
                "skills": {
                    "technology": ["FastAPI"],
                    "programming": ["Python"],
                    "concepts": ["API"],
                },
                "location": "Example City, ST",
                "start": "2024",
                "end": None,
                "links": ["https://example.com/company"],
            }
        ],
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


def _loaded_evidence(
    projects_path: Path,
    skills_path: Path,
    user_path: Path | None = None,
    education_path: Path | None = None,
    experience_path: Path | None = None,
) -> dict:
    if user_path is None:
        user_path = _write_yaml(projects_path.parent / "user.yaml", _user_payload())
    if education_path is None:
        education_path = _write_yaml(
            projects_path.parent / "education.yaml",
            _education_payload(),
        )
    if experience_path is None:
        experience_path = _write_yaml(
            projects_path.parent / "experience.yaml",
            _experience_payload(),
        )
    return {
        "education": load_evidence_yaml(education_path, "education"),
        "experience": load_evidence_yaml(experience_path, "experience"),
        "projects": load_evidence_yaml(projects_path, "projects"),
        "skills": load_evidence_yaml(skills_path, "skills"),
        "user": load_evidence_yaml(user_path, "user"),
    }


def _sample_intermediate_resume_result() -> IntermediateResumeResult:
    return IntermediateResumeResult.model_validate(
        {
            "top": {
                "name": "Example Candidate",
                "phone": "+1 555-0100",
                "email": "candidate_name@example.com",
                "github": "https://github.com/example-candidate",
            },
            "education": [
                {
                    "name": "Example & University",
                    "degree": "Bachelor of Science in Computer Science",
                    "grade": "3.8 GPA",
                    "start": "2020",
                    "end": "2024",
                    "location": "Example City, ST",
                    "relevant_coursework": ["Data Structures", "Algorithms"],
                }
            ],
            "experience": [
                {
                    "name": "Example Company",
                    "role": "Backend Engineer",
                    "bullet_points": ["Designed schema-validated APIs & workers."],
                    "skills": ["FastAPI", "Python"],
                    "location": "Example City, ST",
                    "start": "2024",
                    "end": None,
                }
            ],
            "projects": [
                {
                    "name": "Active Project",
                    "bullet_points": ["Generated bullet for active_project."],
                    "skills": ["FastAPI", "Python", "API"],
                    "links": ["https://example.com/active"],
                }
            ],
            "skills": {
                "technology": ["FastAPI"],
                "programming": ["Python"],
                "concepts": ["API"],
            },
        }
    )


def _install_successful_pipeline_client(monkeypatch, calls: list[dict]) -> None:
    class FakeClient:
        def __init__(self, *, base_url: str, timeout: float):
            assert base_url == "http://jobforge.test"
            assert timeout == 5

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def post(self, endpoint: str, json: dict):
            project_id = json.get("project", {}).get("id")
            experience_id = json.get("experience", {}).get("id")
            calls.append(
                {
                    "endpoint": endpoint,
                    "project_id": project_id,
                    "experience_id": experience_id,
                    "llm_model": json.get("llm_model"),
                }
            )
            if endpoint == "/select-skills":
                return httpx.Response(
                    200,
                    json={
                        "technology": ["FastAPI"],
                        "programming": ["Python"],
                        "concepts": ["API"],
                        "details": {
                            "_llm": {
                                "prompt_tokens": 10,
                                "completion_tokens": 5,
                                "total_tokens": 15,
                                "api_calls": 1,
                                "latency_ms": 100.125,
                            }
                        },
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
                        "details": {
                            "_project_llm": {
                                "prompt_tokens": 20,
                                "completion_tokens": 10,
                                "total_tokens": 30,
                                "api_calls": 1,
                                "latency_ms": 200.25,
                            }
                        },
                    },
                )
            if endpoint == "/generate-bulletpoints":
                evidence_id = project_id or experience_id
                return httpx.Response(
                    200,
                    json={
                        "bullet_points": [f"Generated bullet for {evidence_id}."],
                        "details": {
                            "_bulletpoints_llm": {
                                "prompt_tokens": 4,
                                "completion_tokens": 3,
                                "total_tokens": 7,
                                "api_calls": 1,
                                "latency_ms": 25.0,
                            }
                        },
                    },
                )
            raise AssertionError(f"unexpected endpoint: {endpoint}")

    monkeypatch.setattr("resume_generation.selection.httpx.Client", FakeClient)
    monkeypatch.setattr("resume_generation.bullet_points.httpx.Client", FakeClient)


def test_load_generation_config_returns_typed_config(tmp_path):
    path = _write_yaml(tmp_path / "config.yaml", _config_payload())

    config = load_generation_config(path)

    assert isinstance(config, ResumeGenerationConfig)
    assert config.app.base_url == "http://jobforge.test"
    assert config.skill_selection.llm_model == "skill-model"
    assert config.project_selection.llm_max_output_tokens == 880
    assert config.link_scanning.enabled is False
    assert config.link_scanning.dev_mode is True
    assert config.link_scanning.llm_model == "link-model"
    assert config.link_scanning.llm_max_output_tokens == 660
    assert config.project_bullet_point_generation.llm_model == "project-bullet-model"
    assert config.project_bullet_point_generation.bullet_count_range is not None
    assert config.project_bullet_point_generation.bullet_count_range.min == 2
    assert (
        config.experience_bullet_point_generation.llm_model
        == "experience-bullet-model"
    )
    assert config.experience_bullet_point_generation.bullet_count_range is not None
    assert config.experience_bullet_point_generation.bullet_count_range.min == 1
    assert config.cache.enabled is False
    assert config.cache.force_refresh is False
    assert config.resume_output.path is None
    assert resolve_resume_latex_output_path(config.resume_output.path) == (
        DEFAULT_RESUME_TEX_ARTIFACT_PATH
    )


def test_load_generation_config_accepts_cache_config(tmp_path):
    path = _write_yaml(
        tmp_path / "config.yaml",
        _config_payload(
            cache={
                "enabled": True,
                "path": str(tmp_path / "cache"),
                "force_refresh": True,
            }
        ),
    )

    config = load_generation_config(path)

    assert config.cache.enabled is True
    assert config.cache.path == str(tmp_path / "cache")
    assert config.cache.force_refresh is True


def test_load_generation_config_accepts_resume_output_path(tmp_path):
    output_path = tmp_path / "resume.tex"
    path = _write_yaml(
        tmp_path / "config.yaml",
        _config_payload(resume_output={"path": str(output_path)}),
    )

    config = load_generation_config(path)

    assert config.resume_output.path == str(output_path)
    assert resolve_resume_latex_output_path(config.resume_output.path) == output_path


def test_load_generation_config_defaults_blank_resume_output_path(tmp_path):
    path = _write_yaml(
        tmp_path / "config.yaml",
        _config_payload(resume_output={"path": "   "}),
    )

    config = load_generation_config(path)

    assert config.resume_output.path is None
    assert resolve_resume_latex_output_path(config.resume_output.path) == (
        DEFAULT_RESUME_TEX_ARTIFACT_PATH
    )


def test_resume_generation_stage_cache_reuses_exact_payload(tmp_path):
    cache = ResumeGenerationStageCache(tmp_path / "cache")
    calls: list[str] = []

    first = cache.get_or_store(
        stage="skill_selection",
        payload={"job_role": "Backend Engineer", "top_n": 3},
        fetch=lambda: calls.append("fetch") or {"technology": ["FastAPI"]},
    )
    second = cache.get_or_store(
        stage="skill_selection",
        payload={"top_n": 3, "job_role": "Backend Engineer"},
        fetch=lambda: calls.append("fetch") or {"technology": ["Django"]},
    )

    assert first == {"technology": ["FastAPI"]}
    assert second == {"technology": ["FastAPI"]}
    assert calls == ["fetch"]


def test_resume_generation_stage_cache_invalidates_changed_payload(tmp_path):
    cache = ResumeGenerationStageCache(tmp_path / "cache")
    calls: list[str] = []

    cache.get_or_store(
        stage="skill_selection",
        payload={"job_role": "Backend Engineer"},
        fetch=lambda: calls.append("first") or {"technology": ["FastAPI"]},
    )
    result = cache.get_or_store(
        stage="skill_selection",
        payload={"job_role": "ML Engineer"},
        fetch=lambda: calls.append("second") or {"technology": ["PyTorch"]},
    )

    assert result == {"technology": ["PyTorch"]}
    assert calls == ["first", "second"]


def test_resume_generation_stage_cache_force_refresh_bypasses_read(tmp_path):
    cache = ResumeGenerationStageCache(tmp_path / "cache")
    payload = {"project": {"id": "active-project"}}

    cache.get_or_store(
        stage="project_bullet_points",
        payload=payload,
        fetch=lambda: {"bullet_points": ["Original bullet."]},
        namespace="active-project",
    )

    refreshing_cache = ResumeGenerationStageCache(tmp_path / "cache", force_refresh=True)
    result = refreshing_cache.get_or_store(
        stage="project_bullet_points",
        payload=payload,
        fetch=lambda: {"bullet_points": ["Refreshed bullet."]},
        namespace="active-project",
    )

    assert result == {"bullet_points": ["Refreshed bullet."]}


def test_resume_generation_stage_cache_treats_malformed_entry_as_miss(tmp_path):
    cache = ResumeGenerationStageCache(tmp_path / "cache")
    payload = {"project": {"id": "active-project"}}
    cache_key = cache.cache_key(stage="project_bullet_points", payload=payload)
    entry_path = cache._entry_path(
        stage="project_bullet_points",
        cache_key=cache_key,
        namespace="active-project",
    )
    entry_path.parent.mkdir(parents=True)
    entry_path.write_text("{not valid json", encoding="utf-8")

    result = cache.get_or_store(
        stage="project_bullet_points",
        payload=payload,
        fetch=lambda: {"bullet_points": ["Recovered bullet."]},
        namespace="active-project",
    )

    assert result == {"bullet_points": ["Recovered bullet."]}
    payload_on_disk = json.loads(entry_path.read_text(encoding="utf-8"))
    assert payload_on_disk["data"] == {"bullet_points": ["Recovered bullet."]}


def test_load_generation_config_rejects_invalid_bullet_count_range(tmp_path):
    path = _write_yaml(
        tmp_path / "config.yaml",
        _config_payload(
            project_bullet_point_generation={
                "bullet_count_range": {"min": 0, "max": 4},
                "dev_mode": True,
            }
        ),
    )

    with pytest.raises(ValidationError, match="bullet_count_range.min"):
        load_generation_config(path)


def test_load_generation_config_rejects_legacy_shared_bullet_config(tmp_path):
    path = _write_yaml(
        tmp_path / "config.yaml",
        _config_payload(
            bullet_point_generation={
                "bullet_count_range": {"min": 2, "max": 4},
                "dev_mode": True,
            }
        ),
    )

    with pytest.raises(ValidationError, match="project_bullet_point_generation"):
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
    assert payload["llm_model"] == "project-bullet-model"
    assert payload["llm_max_output_tokens"] == 990
    assert [item.project_id for item in result] == ["active-project"]
    assert result[0].bullet_points == ["Generated bullet for active-project."]


def test_generate_experience_bullet_points_posts_once_per_active_experience(
    monkeypatch,
    tmp_path,
):
    config_path = _write_yaml(tmp_path / "config.yaml", _config_payload())
    job_path = _write_yaml(tmp_path / "job.yaml", _job_target_payload())
    projects_path = _write_yaml(tmp_path / "projects.yaml", _projects_payload())
    skills_path = _write_yaml(tmp_path / "skills.yaml", _skills_payload())
    experience_payload = _experience_payload()
    experience_payload["experience"].append(
        {
            "id": "inactive-role",
            "name": "Inactive Company",
            "role": "Frontend Engineer",
            "summary": "Older inactive experience.",
            "highlights": ["This should not generate."],
            "active": False,
            "skills": {
                "technology": ["Angular"],
                "programming": ["JavaScript"],
                "concepts": ["UI"],
            },
            "location": "Remote",
            "start": "2022",
            "end": "2023",
            "links": None,
        }
    )
    experience_path = _write_yaml(tmp_path / "experience.yaml", experience_payload)
    config = load_generation_config(config_path)
    job_target = load_job_target(job_path)
    experience_file = _loaded_evidence(
        projects_path,
        skills_path,
        experience_path=experience_path,
    )["experience"]
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
                    "bullet_points": [
                        f"Generated bullet for {json['experience']['id']}."
                    ],
                    "details": {"method": "llm"},
                },
            )

    monkeypatch.setattr("resume_generation.bullet_points.httpx.Client", FakeClient)

    result = generate_experience_bullet_points(
        experience=experience_file.experience,
        config=config,
        job_target=job_target,
    )

    assert [endpoint for endpoint, _ in requests] == ["/generate-bulletpoints"]
    payload = requests[0][1]
    assert payload["context"] == {
        "title": "Backend Engineer",
        "description": "Build Python APIs with FastAPI.",
    }
    assert payload["experience"]["id"] == "backend-engineer"
    assert payload["experience"]["role"] == "Backend Engineer"
    assert payload["experience"]["highlights"] == ["Designed schema-validated APIs."]
    assert payload["bullet_count_range"] == {"min": 1, "max": 2}
    assert payload["llm_model"] == "experience-bullet-model"
    assert payload["llm_max_output_tokens"] == 990
    assert [item.experience_id for item in result] == ["backend-engineer"]
    assert result[0].bullet_points == ["Generated bullet for backend-engineer."]


def test_cached_project_bullet_generation_logs_response_source(
    monkeypatch,
    tmp_path,
    caplog,
):
    config_path = _write_yaml(tmp_path / "config.yaml", _config_payload())
    job_path = _write_yaml(tmp_path / "job.yaml", _job_target_payload())
    projects_path = _write_yaml(tmp_path / "projects.yaml", _projects_payload())
    skills_path = _write_yaml(tmp_path / "skills.yaml", _skills_payload())
    config = load_generation_config(config_path)
    job_target = load_job_target(job_path)
    projects_file = _loaded_evidence(projects_path, skills_path)["projects"]
    selected_project = projects_file.projects_by_id()["active-project"]
    cache = ResumeGenerationStageCache(tmp_path / "cache")
    calls: list[str] = []

    class FakeClient:
        def __init__(self, *, base_url: str, timeout: float):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def post(self, endpoint: str, json: dict):
            calls.append(endpoint)
            return httpx.Response(
                200,
                json={
                    "bullet_points": ["Generated bullet for active-project."],
                    "details": {
                        "_bulletpoints_llm": {
                            "prompt_tokens": 6,
                            "completion_tokens": 4,
                            "total_tokens": 10,
                            "api_calls": 1,
                            "latency_ms": 50.5,
                        }
                    },
                },
            )

    monkeypatch.setattr("resume_generation.bullet_points.httpx.Client", FakeClient)

    with caplog.at_level(logging.INFO, logger="resume_generation"):
        generate_project_bullet_points(
            selected_projects=[selected_project],
            config=config,
            job_target=job_target,
            cache=cache,
        )
        generate_project_bullet_points(
            selected_projects=[selected_project],
            config=config,
            job_target=job_target,
            cache=cache,
        )

    response_records = [
        record
        for record in caplog.records
        if getattr(record, "event", None) == "resume_generation_stage_response"
    ]
    assert calls == ["/generate-bulletpoints"]
    assert [
        (record.stage, record.source, record.cache_status, record.endpoint)
        for record in response_records
    ] == [
        ("project_bullet_points", "http", "miss", "/generate-bulletpoints"),
        ("project_bullet_points", "cache", "hit", "/generate-bulletpoints"),
    ]
    assert [
        (
            record.prompt_tokens,
            record.completion_tokens,
            record.total_tokens,
            record.api_calls,
            record.latency_ms,
        )
        for record in response_records
    ] == [
        (6, 4, 10, 1, 50.5),
        (6, 4, 10, 1, 50.5),
    ]
    assert all(record.cache_key for record in response_records)


def test_extract_response_token_usage_reads_stage_metadata():
    skill_usage = extract_response_token_usage(
        "skill_selection",
        {
            "details": {
                "_llm": {
                    "prompt_tokens": "11",
                    "completion_tokens": 7,
                    "total_tokens": 18,
                    "api_calls": 1,
                    "latency_ms": "31.25",
                }
            }
        },
    )
    project_usage = extract_response_token_usage(
        "project_selection",
        {"details": {"_project_llm": {"total_tokens": 22}}},
    )
    link_usage = extract_response_token_usage(
        "link_scanning",
        {"details": {"_link_scanning_llm": {"total_tokens": 33}}},
    )
    bullet_usage = extract_response_token_usage(
        "experience_bullet_points",
        {"details": {"_bulletpoints_llm": {"total_tokens": 44}}},
    )
    missing_usage = extract_response_token_usage(
        "project_bullet_points",
        {"details": {"_bulletpoints_llm": {"total_tokens": "not-a-number"}}},
    )

    assert skill_usage.model_dump() == {
        "prompt_tokens": 11,
        "completion_tokens": 7,
        "total_tokens": 18,
        "api_calls": 1,
        "latency_ms": 31.25,
    }
    assert project_usage.total_tokens == 22
    assert link_usage.total_tokens == 33
    assert bullet_usage.total_tokens == 44
    assert missing_usage.total_tokens == 0


def test_enrich_projects_with_link_scanning_posts_linked_projects_and_merges_patch(
    monkeypatch,
    tmp_path,
):
    config_path = _write_yaml(
        tmp_path / "config.yaml",
        _config_payload(
            link_scanning={
                "enabled": True,
                "dev_mode": True,
                "llm_model": "link-model",
                "llm_max_output_tokens": 660,
            }
        ),
    )
    job_path = _write_yaml(tmp_path / "job.yaml", _job_target_payload())
    projects_path = _write_yaml(tmp_path / "projects.yaml", _projects_payload())
    skills_path = _write_yaml(tmp_path / "skills.yaml", _skills_payload())
    config = load_generation_config(config_path)
    job_target = load_job_target(job_path)
    projects_file = _loaded_evidence(projects_path, skills_path)["projects"]
    linked_project = projects_file.projects_by_id()["active-project"]
    unlinked_project = projects_file.projects_by_id()["inactive-project"]
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
                    "project_id": json["project"]["id"],
                    "added_highlights": [
                        {
                            "text": "Scanned README confirms API orchestration.",
                            "source_url": "https://example.com/active",
                        }
                    ],
                    "details": {"method": "llm"},
                },
            )

    monkeypatch.setattr("resume_generation.link_scanning.httpx.Client", FakeClient)

    result = enrich_projects_with_link_scanning(
        selected_projects=[linked_project, unlinked_project],
        config=config,
        job_target=job_target,
    )

    assert [endpoint for endpoint, _ in requests] == ["/scan-link"]
    payload = requests[0][1]
    assert payload["project"]["id"] == "active-project"
    assert payload["dev_mode"] is True
    assert payload["llm_model"] == "link-model"
    assert payload["llm_max_output_tokens"] == 660
    assert result[0].highlights == [
        "Built the service.",
        "Scanned README confirms API orchestration.",
    ]
    assert result[0].skills.technology == ["FastAPI"]
    assert result[0].skills.programming == ["Python"]
    assert result[1].id == "inactive-project"


def test_assemble_intermediate_resume_result_builds_deterministic_schema(tmp_path):
    config_path = _write_yaml(tmp_path / "config.yaml", _config_payload())
    job_path = _write_yaml(tmp_path / "job.yaml", _job_target_payload())
    projects_path = _write_yaml(tmp_path / "projects.yaml", _projects_payload())
    skills_path = _write_yaml(tmp_path / "skills.yaml", _skills_payload())
    user_path = _write_yaml(
        tmp_path / "user.yaml",
        {
            **_user_payload(),
            "website": "https://example.com",
        },
    )
    experience_payload = _experience_payload()
    experience_payload["experience"][0]["skills"] = {
        "technology": ["FastAPI", "Docker"],
        "programming": ["Python", "SQL"],
        "concepts": ["API", "Testing"],
    }
    experience_payload["experience"].append(
        {
            "id": "inactive-role",
            "name": "Inactive Company",
            "role": "Frontend Engineer",
            "summary": "Older inactive experience.",
            "highlights": ["This should not appear."],
            "active": False,
            "skills": {
                "technology": ["Angular"],
                "programming": ["JavaScript"],
                "concepts": ["UI"],
            },
            "location": "Remote",
            "start": "2022",
            "end": "2023",
            "links": None,
        }
    )
    education_path = _write_yaml(tmp_path / "education.yaml", _education_payload())
    experience_path = _write_yaml(tmp_path / "experience.yaml", experience_payload)
    loaded_evidence = _loaded_evidence(
        projects_path,
        skills_path,
        user_path=user_path,
        education_path=education_path,
        experience_path=experience_path,
    )
    projects_file = loaded_evidence["projects"]
    unlinked_project = projects_file.projects_by_id()["inactive-project"]
    linked_project = projects_file.projects_by_id()["active-project"]
    selection_context = ResumeSelectionContext(
        job_target=load_job_target(job_path),
        selected_skills=SkillSelectionResult(
            technology=["FastAPI", "Django"],
            programming=["Python"],
            concepts=["API"],
        ),
        project_selection=ProjectSelectionResult(
            selected_project_ids=["inactive-project", "active-project"],
            ranked_projects=[
                {"project_id": "inactive-project", "score": 1.0, "method": "baseline"},
                {"project_id": "active-project", "score": 0.9, "method": "baseline"},
            ],
        ),
        selected_projects=[unlinked_project, linked_project],
        config_path=config_path,
        job_target_path=job_path,
        evidence_paths={
            "projects": projects_path,
            "skills": skills_path,
            "user": user_path,
            "education": education_path,
            "experience": experience_path,
        },
    )

    result = assemble_intermediate_resume_result(
        user_info=loaded_evidence["user"],
        education=loaded_evidence["education"],
        experience=loaded_evidence["experience"],
        selection_context=selection_context,
        selected_projects=[unlinked_project, linked_project],
        project_bullet_points=[
            ProjectBulletPointResult(
                project_id="inactive-project",
                bullet_points=["Generated bullet for inactive-project."],
            ),
            ProjectBulletPointResult(
                project_id="active-project",
                bullet_points=["Generated bullet for active-project."],
            ),
        ],
        experience_bullet_points=[
            ExperienceBulletPointResult(
                experience_id="backend-engineer",
                bullet_points=["Generated bullet for backend-engineer."],
            )
        ],
    )

    assert result.top.model_dump() == {
        "name": "Example Candidate",
        "phone": "+1 555-0100",
        "email": "candidate@example.com",
        "github": "https://github.com/example-candidate",
        "website": "https://example.com",
        "linkedin": "https://www.linkedin.com/in/example-candidate",
    }
    assert [item.name for item in result.education] == ["Example University"]
    assert result.education[0].relevant_coursework == ["Data Structures", "Algorithms"]
    assert [item.name for item in result.experience] == ["Example Company"]
    assert result.experience[0].role == "Backend Engineer"
    assert result.experience[0].bullet_points == ["Generated bullet for backend-engineer."]
    assert result.experience[0].skills == [
        "FastAPI",
        "Docker",
        "Python",
        "SQL",
        "API",
        "Testing",
    ]
    assert [project.name for project in result.projects] == [
        "Inactive Project",
        "Active Project",
    ]
    assert result.projects[0].bullet_points == ["Generated bullet for inactive-project."]
    assert result.projects[0].skills == ["Angular", "JavaScript", "UI"]
    assert result.projects[0].links == []
    assert result.projects[1].links == ["https://example.com/active"]
    assert result.skills.model_dump() == {
        "technology": ["FastAPI", "Django"],
        "programming": ["Python"],
        "concepts": ["API"],
    }


def test_write_resume_result_artifact_writes_human_readable_json(tmp_path):
    resume_result = IntermediateResumeResult.model_validate(
        {
            "top": {
                "name": "Example Candidate",
                "phone": "+1 555-0100",
                "email": "candidate@example.com",
                "github": "https://github.com/example-candidate",
            },
            "education": [
                {
                    "name": "Example University",
                    "degree": "Bachelor of Science in Computer Science",
                    "grade": "3.8 GPA",
                    "start": "2020",
                    "end": "2024",
                    "location": "Example City, ST",
                    "relevant_coursework": ["Data Structures"],
                }
            ],
            "experience": [
                {
                    "name": "Example Company",
                    "role": "Backend Engineer",
                    "bullet_points": ["Designed schema-validated APIs."],
                    "skills": ["FastAPI", "Python"],
                    "location": "Example City, ST",
                    "start": "2024",
                }
            ],
            "projects": [
                {
                    "name": "Active Project",
                    "bullet_points": ["Generated bullet for active-project."],
                    "skills": ["FastAPI", "Python", "API"],
                    "links": ["https://example.com/active"],
                }
            ],
            "skills": {
                "technology": ["FastAPI"],
                "programming": ["Python"],
                "concepts": ["API"],
            },
        }
    )
    artifact_path = tmp_path / "artifacts" / "resume_result.json"

    written_path = write_resume_result_artifact(resume_result, artifact_path)

    assert written_path == artifact_path
    raw_json = artifact_path.read_text(encoding="utf-8")
    assert raw_json.endswith("\n")
    assert '\n  "top": {' in raw_json
    payload = json.loads(raw_json)
    assert list(payload) == ["top", "education", "experience", "projects", "skills"]
    assert payload["top"]["name"] == "Example Candidate"
    assert payload["projects"][0]["bullet_points"] == [
        "Generated bullet for active-project."
    ]


def test_latex_escape_escapes_reserved_characters():
    assert latex_escape("&%$_#{}") == r"\&\%\$\_\#\{\}"
    assert latex_escape("Path \\ value ~ caret ^") == (
        r"Path \textbackslash{} value \textasciitilde{} caret \textasciicircum{}"
    )


def test_render_resume_latex_uses_template_sections_and_runtime_result():
    resume_result = _sample_intermediate_resume_result()

    rendered = render_resume_latex(resume_result)

    assert rendered.startswith("\\documentclass[letterpaper,9pt]{article}")
    assert rendered.endswith("\\end{document}\n")
    assert "\\section{Education}" in rendered
    assert "\\section{Experience}" in rendered
    assert "\\section{Projects}" in rendered
    assert "\\section{Technical Skills}" in rendered
    assert r"\textbf{\Large \scshape Example Candidate}" in rendered
    assert r"{\seticon{faEnvelope} candidate\_name@example.com}" in rendered
    assert r"{\seticon{faGithub} \underline{github.com/example-candidate}}" in rendered
    assert "faLinkedin" not in rendered
    assert "faGlobe" not in rendered
    assert r"{Example \& University}{2020 -- 2024}" in rendered
    assert (
        r"\resumeItem{\textbf{Relevant Coursework:} Data Structures, Algorithms}"
        in rendered
    )
    assert (
        r"{Backend Engineer $|$ \emph{FastAPI, Python}}{Example City, ST}"
        in rendered
    )
    assert r"\resumeItem{Designed schema-validated APIs \& workers.}" in rendered
    assert (
        r"{\textbf{Active Project} $|$ \emph{FastAPI, Python, API}}{}"
        in rendered
    )
    assert r"\resumeItem{Generated bullet for active\_project.}" in rendered
    assert (
        rendered.index("\\section{Education}")
        < rendered.index("\\section{Experience}")
        < rendered.index("\\section{Projects}")
        < rendered.index("\\section{Technical Skills}")
    )


def test_write_resume_latex_artifact_writes_tex_file(tmp_path):
    resume_result = _sample_intermediate_resume_result()
    artifact_path = tmp_path / "artifacts" / "resume.tex"

    written_path = write_resume_latex_artifact(resume_result, artifact_path)

    assert written_path == artifact_path
    rendered = artifact_path.read_text(encoding="utf-8")
    assert rendered.startswith("\\documentclass[letterpaper,9pt]{article}")
    assert rendered.endswith("\\end{document}\n")
    assert "\\section{Projects}" in rendered


def test_write_resume_latex_from_config_writes_configured_output(
    tmp_path,
    caplog,
):
    resume_result = _sample_intermediate_resume_result()
    output_path = tmp_path / "out" / "resume.tex"
    config_path = _write_yaml(
        tmp_path / "config.yaml",
        _config_payload(resume_output={"path": str(output_path)}),
    )

    with caplog.at_level(logging.INFO, logger="resume_generation"):
        written_path = write_resume_latex_from_config(
            resume_result,
            config_path=config_path,
        )

    assert written_path == output_path
    assert output_path.read_text(encoding="utf-8").endswith("\\end{document}\n")
    records = [
        record
        for record in caplog.records
        if getattr(record, "event", None) == "resume_generation_latex_artifact_written"
    ]
    assert len(records) == 1
    assert records[0].path == str(output_path)


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


def test_resume_generation_pipeline_requires_loaded_education(monkeypatch, tmp_path):
    config_path = _write_yaml(tmp_path / "config.yaml", _config_payload())
    job_path = _write_yaml(tmp_path / "job.yaml", _job_target_payload())
    projects_path = _write_yaml(tmp_path / "projects.yaml", _projects_payload())
    skills_path = _write_yaml(tmp_path / "skills.yaml", _skills_payload())
    loaded_evidence = _loaded_evidence(projects_path, skills_path)
    del loaded_evidence["education"]
    calls: list[str] = []

    class FakeClient:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def post(self, endpoint: str, json: dict):
            calls.append(endpoint)
            raise AssertionError(f"unexpected endpoint: {endpoint}")

    monkeypatch.setattr("resume_generation.selection.httpx.Client", FakeClient)
    monkeypatch.setattr(
        "resume_generation.main.load_registered_evidence",
        lambda paths=None: loaded_evidence,
    )

    with pytest.raises(TypeError, match="valid education file"):
        run_resume_generation_pipeline(
            config_path=config_path,
            job_target_path=job_path,
            evidence_paths={
                "projects": projects_path,
                "skills": skills_path,
            },
        )

    assert calls == []


def test_resume_generation_pipeline_rejects_invalid_loaded_education(monkeypatch, tmp_path):
    config_path = _write_yaml(tmp_path / "config.yaml", _config_payload())
    job_path = _write_yaml(tmp_path / "job.yaml", _job_target_payload())
    projects_path = _write_yaml(tmp_path / "projects.yaml", _projects_payload())
    skills_path = _write_yaml(tmp_path / "skills.yaml", _skills_payload())
    user_path = _write_yaml(tmp_path / "user.yaml", _user_payload())
    loaded_evidence = _loaded_evidence(projects_path, skills_path, user_path=user_path)
    loaded_evidence["education"] = load_evidence_yaml(user_path, "user")
    calls: list[str] = []

    class FakeClient:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def post(self, endpoint: str, json: dict):
            calls.append(endpoint)
            raise AssertionError(f"unexpected endpoint: {endpoint}")

    monkeypatch.setattr("resume_generation.selection.httpx.Client", FakeClient)
    monkeypatch.setattr(
        "resume_generation.main.load_registered_evidence",
        lambda paths=None: loaded_evidence,
    )

    with pytest.raises(TypeError, match="valid education file"):
        run_resume_generation_pipeline(
            config_path=config_path,
            job_target_path=job_path,
            evidence_paths={
                "projects": projects_path,
                "skills": skills_path,
            },
        )

    assert calls == []


def test_resume_generation_pipeline_requires_loaded_experience(monkeypatch, tmp_path):
    config_path = _write_yaml(tmp_path / "config.yaml", _config_payload())
    job_path = _write_yaml(tmp_path / "job.yaml", _job_target_payload())
    projects_path = _write_yaml(tmp_path / "projects.yaml", _projects_payload())
    skills_path = _write_yaml(tmp_path / "skills.yaml", _skills_payload())
    loaded_evidence = _loaded_evidence(projects_path, skills_path)
    del loaded_evidence["experience"]
    calls: list[str] = []

    class FakeClient:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def post(self, endpoint: str, json: dict):
            calls.append(endpoint)
            raise AssertionError(f"unexpected endpoint: {endpoint}")

    monkeypatch.setattr("resume_generation.selection.httpx.Client", FakeClient)
    monkeypatch.setattr(
        "resume_generation.main.load_registered_evidence",
        lambda paths=None: loaded_evidence,
    )

    with pytest.raises(TypeError, match="valid experience file"):
        run_resume_generation_pipeline(
            config_path=config_path,
            job_target_path=job_path,
            evidence_paths={
                "projects": projects_path,
                "skills": skills_path,
            },
        )

    assert calls == []


def test_resume_generation_pipeline_rejects_invalid_loaded_experience(monkeypatch, tmp_path):
    config_path = _write_yaml(tmp_path / "config.yaml", _config_payload())
    job_path = _write_yaml(tmp_path / "job.yaml", _job_target_payload())
    projects_path = _write_yaml(tmp_path / "projects.yaml", _projects_payload())
    skills_path = _write_yaml(tmp_path / "skills.yaml", _skills_payload())
    user_path = _write_yaml(tmp_path / "user.yaml", _user_payload())
    loaded_evidence = _loaded_evidence(projects_path, skills_path, user_path=user_path)
    loaded_evidence["experience"] = load_evidence_yaml(user_path, "user")
    calls: list[str] = []

    class FakeClient:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def post(self, endpoint: str, json: dict):
            calls.append(endpoint)
            raise AssertionError(f"unexpected endpoint: {endpoint}")

    monkeypatch.setattr("resume_generation.selection.httpx.Client", FakeClient)
    monkeypatch.setattr(
        "resume_generation.main.load_registered_evidence",
        lambda paths=None: loaded_evidence,
    )

    with pytest.raises(TypeError, match="valid experience file"):
        run_resume_generation_pipeline(
            config_path=config_path,
            job_target_path=job_path,
            evidence_paths={
                "projects": projects_path,
                "skills": skills_path,
            },
        )

    assert calls == []


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
                evidence = json.get("project") or json.get("experience")
                return httpx.Response(
                    200,
                    json={
                        "bullet_points": [f"Generated bullet for {evidence['id']}."],
                    },
                )
            raise AssertionError(f"unexpected endpoint: {endpoint}")

    monkeypatch.setattr("resume_generation.selection.httpx.Client", FakeClient)
    monkeypatch.setattr("resume_generation.bullet_points.httpx.Client", FakeClient)
    monkeypatch.setattr(
        "resume_generation.main.load_registered_evidence",
        lambda paths=None: loaded_evidence,
    )
    assembly_calls: list[dict] = []

    def fake_assemble_intermediate_resume_result(**kwargs):
        calls.append("assemble")
        assembly_calls.append(kwargs)
        return IntermediateResumeResult.model_validate(
            {
                "top": {
                    "name": "Example Candidate",
                    "phone": "+1 555-0100",
                    "email": "candidate@example.com",
                },
                "education": [
                    {
                        "name": "Example University",
                        "degree": "Bachelor of Science in Computer Science",
                        "grade": "3.8 GPA",
                        "start": "2020",
                        "end": "2024",
                        "location": "Example City, ST",
                        "relevant_coursework": ["Data Structures"],
                    }
                ],
                "experience": [
                    {
                        "name": "Example Company",
                        "role": "Backend Engineer",
                        "bullet_points": ["Designed schema-validated APIs."],
                        "skills": ["FastAPI", "Python"],
                        "location": "Example City, ST",
                        "start": "2024",
                    }
                ],
                "projects": [
                    {
                        "name": "Active Project",
                        "bullet_points": ["Generated bullet for active-project."],
                        "skills": ["FastAPI", "Python", "API"],
                        "links": ["https://example.com/active"],
                    }
                ],
                "skills": {
                    "technology": ["FastAPI"],
                    "programming": ["Python"],
                    "concepts": ["API"],
                },
            }
        )

    monkeypatch.setattr(
        "resume_generation.main.assemble_intermediate_resume_result",
        fake_assemble_intermediate_resume_result,
    )
    artifact_path = tmp_path / "artifacts" / "resume_result.json"

    result = run_resume_generation_pipeline(
        config_path=config_path,
        job_target_path=job_path,
        evidence_paths={
            "projects": projects_path,
            "skills": skills_path,
        },
        resume_result_artifact_path=artifact_path,
    )

    assert calls == [
        "/select-skills",
        "/select-projects",
        "/generate-bulletpoints",
        "/generate-bulletpoints",
        "assemble",
    ]
    assert result.top.name == "Example Candidate"
    artifact_payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact_payload["top"]["name"] == "Example Candidate"
    assert artifact_payload["projects"][0]["bullet_points"] == [
        "Generated bullet for active-project."
    ]
    assert assembly_calls[0]["user_info"].name == "Example Candidate"
    assert assembly_calls[0]["education"].education[0].name == "Example University"
    assert assembly_calls[0]["experience"].experience[0].name == "Example Company"
    assert assembly_calls[0]["selection_context"].selected_skills.technology == ["FastAPI"]
    assert [project.id for project in assembly_calls[0]["selected_projects"]] == [
        "active-project"
    ]
    assert [item.project_id for item in assembly_calls[0]["project_bullet_points"]] == [
        "active-project"
    ]
    assert assembly_calls[0]["project_bullet_points"][0].bullet_points == [
        "Generated bullet for active-project."
    ]
    assert [item.experience_id for item in assembly_calls[0]["experience_bullet_points"]] == [
        "backend-engineer"
    ]
    assert assembly_calls[0]["experience_bullet_points"][0].bullet_points == [
        "Generated bullet for backend-engineer."
    ]


def test_resume_generation_pipeline_reuses_cached_stage_results(monkeypatch, tmp_path):
    config_path = _write_yaml(
        tmp_path / "config.yaml",
        _config_payload(
            cache={
                "enabled": True,
                "path": str(tmp_path / "cache"),
                "force_refresh": False,
            }
        ),
    )
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
                        "bullet_points": ["Cached generated bullet."],
                    },
                )
            raise AssertionError(f"unexpected endpoint: {endpoint}")

    monkeypatch.setattr("resume_generation.selection.httpx.Client", FakeClient)
    monkeypatch.setattr("resume_generation.bullet_points.httpx.Client", FakeClient)
    monkeypatch.setattr(
        "resume_generation.main.load_registered_evidence",
        lambda paths=None: loaded_evidence,
    )

    for _ in range(2):
        run_resume_generation_pipeline(
            config_path=config_path,
            job_target_path=job_path,
            evidence_paths={
                "projects": projects_path,
                "skills": skills_path,
            },
        )

    assert calls == [
        "/select-skills",
        "/select-projects",
        "/generate-bulletpoints",
        "/generate-bulletpoints",
    ]


def test_experience_bullet_model_change_does_not_regenerate_project_bullets(
    monkeypatch,
    tmp_path,
):
    cache_config = {
        "enabled": True,
        "path": str(tmp_path / "cache"),
        "force_refresh": False,
    }
    first_config_path = _write_yaml(
        tmp_path / "first-config.yaml",
        _config_payload(cache=cache_config),
    )
    second_config = _config_payload(cache=cache_config)
    second_config["experience_bullet_point_generation"][
        "llm_model"
    ] = "experience-bullet-model-v2"
    second_config_path = _write_yaml(tmp_path / "second-config.yaml", second_config)
    job_path = _write_yaml(tmp_path / "job.yaml", _job_target_payload())
    projects_path = _write_yaml(tmp_path / "projects.yaml", _projects_payload())
    skills_path = _write_yaml(tmp_path / "skills.yaml", _skills_payload())
    loaded_evidence = _loaded_evidence(projects_path, skills_path)
    calls: list[dict] = []

    _install_successful_pipeline_client(monkeypatch, calls)
    monkeypatch.setattr(
        "resume_generation.main.load_registered_evidence",
        lambda paths=None: loaded_evidence,
    )

    run_resume_generation_pipeline(
        config_path=first_config_path,
        job_target_path=job_path,
        evidence_paths={"projects": projects_path, "skills": skills_path},
    )
    run_resume_generation_pipeline(
        config_path=second_config_path,
        job_target_path=job_path,
        evidence_paths={"projects": projects_path, "skills": skills_path},
    )

    assert [
        (call["endpoint"], call["project_id"], call["experience_id"], call["llm_model"])
        for call in calls
    ] == [
        ("/select-skills", None, None, "skill-model"),
        ("/select-projects", None, None, "project-model"),
        ("/generate-bulletpoints", "active-project", None, "project-bullet-model"),
        (
            "/generate-bulletpoints",
            None,
            "backend-engineer",
            "experience-bullet-model",
        ),
        (
            "/generate-bulletpoints",
            None,
            "backend-engineer",
            "experience-bullet-model-v2",
        ),
    ]


def test_project_bullet_model_change_does_not_regenerate_experience_bullets(
    monkeypatch,
    tmp_path,
):
    cache_config = {
        "enabled": True,
        "path": str(tmp_path / "cache"),
        "force_refresh": False,
    }
    first_config_path = _write_yaml(
        tmp_path / "first-config.yaml",
        _config_payload(cache=cache_config),
    )
    second_config = _config_payload(cache=cache_config)
    second_config["project_bullet_point_generation"][
        "llm_model"
    ] = "project-bullet-model-v2"
    second_config_path = _write_yaml(tmp_path / "second-config.yaml", second_config)
    job_path = _write_yaml(tmp_path / "job.yaml", _job_target_payload())
    projects_path = _write_yaml(tmp_path / "projects.yaml", _projects_payload())
    skills_path = _write_yaml(tmp_path / "skills.yaml", _skills_payload())
    loaded_evidence = _loaded_evidence(projects_path, skills_path)
    calls: list[dict] = []

    _install_successful_pipeline_client(monkeypatch, calls)
    monkeypatch.setattr(
        "resume_generation.main.load_registered_evidence",
        lambda paths=None: loaded_evidence,
    )

    run_resume_generation_pipeline(
        config_path=first_config_path,
        job_target_path=job_path,
        evidence_paths={"projects": projects_path, "skills": skills_path},
    )
    run_resume_generation_pipeline(
        config_path=second_config_path,
        job_target_path=job_path,
        evidence_paths={"projects": projects_path, "skills": skills_path},
    )

    assert [
        (call["endpoint"], call["project_id"], call["experience_id"], call["llm_model"])
        for call in calls
    ] == [
        ("/select-skills", None, None, "skill-model"),
        ("/select-projects", None, None, "project-model"),
        ("/generate-bulletpoints", "active-project", None, "project-bullet-model"),
        (
            "/generate-bulletpoints",
            None,
            "backend-engineer",
            "experience-bullet-model",
        ),
        ("/generate-bulletpoints", "active-project", None, "project-bullet-model-v2"),
    ]


def test_skill_evidence_change_only_invalidates_skill_selection(
    monkeypatch,
    tmp_path,
):
    config_path = _write_yaml(
        tmp_path / "config.yaml",
        _config_payload(
            cache={
                "enabled": True,
                "path": str(tmp_path / "cache"),
                "force_refresh": False,
            }
        ),
    )
    job_path = _write_yaml(tmp_path / "job.yaml", _job_target_payload())
    projects_path = _write_yaml(tmp_path / "projects.yaml", _projects_payload())
    first_skills_path = _write_yaml(tmp_path / "first-skills.yaml", _skills_payload())
    second_skills = _skills_payload()
    second_skills["skills"]["technology"].append("Redis")
    second_skills_path = _write_yaml(tmp_path / "second-skills.yaml", second_skills)
    evidence_by_skills_path = {
        first_skills_path: _loaded_evidence(projects_path, first_skills_path),
        second_skills_path: _loaded_evidence(projects_path, second_skills_path),
    }
    calls: list[dict] = []

    _install_successful_pipeline_client(monkeypatch, calls)

    def fake_load_registered_evidence(paths=None):
        assert paths is not None
        return evidence_by_skills_path[Path(paths["skills"])]

    monkeypatch.setattr(
        "resume_generation.main.load_registered_evidence",
        fake_load_registered_evidence,
    )

    run_resume_generation_pipeline(
        config_path=config_path,
        job_target_path=job_path,
        evidence_paths={"projects": projects_path, "skills": first_skills_path},
    )
    run_resume_generation_pipeline(
        config_path=config_path,
        job_target_path=job_path,
        evidence_paths={"projects": projects_path, "skills": second_skills_path},
    )

    assert [
        (call["endpoint"], call["project_id"], call["experience_id"])
        for call in calls
    ] == [
        ("/select-skills", None, None),
        ("/select-projects", None, None),
        ("/generate-bulletpoints", "active-project", None),
        ("/generate-bulletpoints", None, "backend-engineer"),
        ("/select-skills", None, None),
    ]


def test_resume_generation_pipeline_logs_stage_events(monkeypatch, tmp_path, caplog):
    config_path = _write_yaml(tmp_path / "config.yaml", _config_payload())
    job_path = _write_yaml(tmp_path / "job.yaml", _job_target_payload())
    projects_path = _write_yaml(tmp_path / "projects.yaml", _projects_payload())
    skills_path = _write_yaml(tmp_path / "skills.yaml", _skills_payload())
    loaded_evidence = _loaded_evidence(projects_path, skills_path)
    calls: list[dict] = []

    _install_successful_pipeline_client(monkeypatch, calls)
    monkeypatch.setattr(
        "resume_generation.main.load_registered_evidence",
        lambda paths=None: loaded_evidence,
    )

    with caplog.at_level(logging.INFO, logger="resume_generation"):
        run_resume_generation_pipeline(
            config_path=config_path,
            job_target_path=job_path,
            evidence_paths={"projects": projects_path, "skills": skills_path},
        )

    stage_events = [
        (record.event, getattr(record, "stage", None))
        for record in caplog.records
        if getattr(record, "event", None)
        in {
            "resume_generation_pipeline_start",
            "resume_generation_pipeline_complete",
            "resume_generation_stage_start",
            "resume_generation_stage_complete",
            "resume_generation_stage_skipped",
            "resume_generation_artifact_written",
        }
    ]
    assert ("resume_generation_pipeline_start", None) in stage_events
    assert ("resume_generation_stage_start", "selection") in stage_events
    assert ("resume_generation_stage_complete", "selection") in stage_events
    assert ("resume_generation_stage_skipped", "link_scanning") in stage_events
    assert ("resume_generation_stage_start", "project_bullet_points") in stage_events
    assert ("resume_generation_stage_complete", "project_bullet_points") in stage_events
    assert ("resume_generation_stage_start", "experience_bullet_points") in stage_events
    assert ("resume_generation_stage_complete", "experience_bullet_points") in stage_events
    assert ("resume_generation_stage_complete", "assembly") in stage_events
    assert ("resume_generation_artifact_written", None) in stage_events
    assert ("resume_generation_pipeline_complete", None) in stage_events
    skipped_link_records = [
        record
        for record in caplog.records
        if getattr(record, "event", None) == "resume_generation_stage_skipped"
        and getattr(record, "stage", None) == "link_scanning"
    ]
    assert skipped_link_records[0].total_tokens == 0


def test_resume_generation_pipeline_logs_token_usage_summary(
    monkeypatch,
    tmp_path,
    caplog,
):
    config_path = _write_yaml(tmp_path / "config.yaml", _config_payload())
    job_path = _write_yaml(tmp_path / "job.yaml", _job_target_payload())
    projects_path = _write_yaml(tmp_path / "projects.yaml", _projects_payload())
    skills_path = _write_yaml(tmp_path / "skills.yaml", _skills_payload())
    loaded_evidence = _loaded_evidence(projects_path, skills_path)
    calls: list[dict] = []

    _install_successful_pipeline_client(monkeypatch, calls)
    monkeypatch.setattr(
        "resume_generation.main.load_registered_evidence",
        lambda paths=None: loaded_evidence,
    )

    with caplog.at_level(logging.INFO, logger="resume_generation"):
        run_resume_generation_pipeline(
            config_path=config_path,
            job_target_path=job_path,
            evidence_paths={"projects": projects_path, "skills": skills_path},
        )

    stage_complete = {
        record.stage: record
        for record in caplog.records
        if getattr(record, "event", None) == "resume_generation_stage_complete"
    }
    assert stage_complete["selection"].total_tokens == 45
    assert stage_complete["project_bullet_points"].total_tokens == 7
    assert stage_complete["experience_bullet_points"].total_tokens == 7
    assert stage_complete["assembly"].total_tokens == 0

    summaries = [
        record
        for record in caplog.records
        if getattr(record, "event", None) == "resume_generation_token_usage_summary"
    ]
    assert len(summaries) == 1
    summary = summaries[0]
    assert summary.stages["selection"]["total_tokens"] == 45
    assert summary.stages["skill_selection"]["total_tokens"] == 15
    assert summary.stages["project_selection"]["total_tokens"] == 30
    assert summary.stages["link_scanning"]["total_tokens"] == 0
    assert summary.stages["project_bullet_points"]["total_tokens"] == 7
    assert summary.stages["experience_bullet_points"]["total_tokens"] == 7
    assert summary.stages["assembly"]["total_tokens"] == 0
    assert summary.total["total_tokens"] == 59
    assert summary.total["api_calls"] == 4


def test_resume_generation_pipeline_cache_misses_when_job_target_changes(
    monkeypatch,
    tmp_path,
):
    config_path = _write_yaml(
        tmp_path / "config.yaml",
        _config_payload(
            cache={
                "enabled": True,
                "path": str(tmp_path / "cache"),
                "force_refresh": False,
            }
        ),
    )
    first_job_path = _write_yaml(tmp_path / "first-job.yaml", _job_target_payload())
    second_job_path = _write_yaml(
        tmp_path / "second-job.yaml",
        _job_target_payload(title="ML Engineer"),
    )
    projects_path = _write_yaml(tmp_path / "projects.yaml", _projects_payload())
    skills_path = _write_yaml(tmp_path / "skills.yaml", _skills_payload())
    loaded_evidence = _loaded_evidence(projects_path, skills_path)
    calls: list[str] = []

    class FakeClient:
        def __init__(self, *, base_url: str, timeout: float):
            pass

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
                    json={"bullet_points": ["Generated bullet."]},
                )
            raise AssertionError(f"unexpected endpoint: {endpoint}")

    monkeypatch.setattr("resume_generation.selection.httpx.Client", FakeClient)
    monkeypatch.setattr("resume_generation.bullet_points.httpx.Client", FakeClient)
    monkeypatch.setattr(
        "resume_generation.main.load_registered_evidence",
        lambda paths=None: loaded_evidence,
    )

    run_resume_generation_pipeline(
        config_path=config_path,
        job_target_path=first_job_path,
        evidence_paths={
            "projects": projects_path,
            "skills": skills_path,
        },
    )
    run_resume_generation_pipeline(
        config_path=config_path,
        job_target_path=second_job_path,
        evidence_paths={
            "projects": projects_path,
            "skills": skills_path,
        },
    )

    assert calls == [
        "/select-skills",
        "/select-projects",
        "/generate-bulletpoints",
        "/generate-bulletpoints",
        "/select-skills",
        "/select-projects",
        "/generate-bulletpoints",
        "/generate-bulletpoints",
    ]


def test_resume_generation_pipeline_resumes_after_project_bullet_failure(
    monkeypatch,
    tmp_path,
):
    config_path = _write_yaml(
        tmp_path / "config.yaml",
        _config_payload(
            cache={
                "enabled": True,
                "path": str(tmp_path / "cache"),
                "force_refresh": False,
            }
        ),
    )
    job_path = _write_yaml(tmp_path / "job.yaml", _job_target_payload())
    projects_payload = _projects_payload()
    projects_payload["projects"].append(
        {
            "id": "second-project",
            "name": "Second Project",
            "summary": "Second FastAPI backend service.",
            "highlights": ["Built another service."],
            "active": True,
            "skills": {
                "technology": ["FastAPI"],
                "programming": ["Python"],
                "concepts": ["API"],
            },
            "links": None,
        }
    )
    projects_path = _write_yaml(tmp_path / "projects.yaml", projects_payload)
    skills_path = _write_yaml(tmp_path / "skills.yaml", _skills_payload())
    loaded_evidence = _loaded_evidence(projects_path, skills_path)
    calls: list[tuple[str, str | None]] = []
    fail_second_project = True

    class FakeClient:
        def __init__(self, *, base_url: str, timeout: float):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def post(self, endpoint: str, json: dict):
            nonlocal fail_second_project
            project_id = json.get("project", {}).get("id")
            experience_id = json.get("experience", {}).get("id")
            evidence_id = project_id or experience_id
            calls.append((endpoint, evidence_id))
            if endpoint == "/select-skills":
                return httpx.Response(
                    200,
                    json={
                        "technology": ["FastAPI"],
                        "programming": ["Python"],
                        "concepts": ["API"],
                    },
                )
            if endpoint == "/select-projects":
                return httpx.Response(
                    200,
                    json={
                        "selected_project_ids": ["active-project", "second-project"],
                        "ranked_projects": [
                            {
                                "project_id": "active-project",
                                "score": 1.0,
                                "method": "llm",
                            },
                            {
                                "project_id": "second-project",
                                "score": 0.9,
                                "method": "llm",
                            },
                        ],
                    },
                )
            if endpoint == "/generate-bulletpoints":
                if project_id == "second-project" and fail_second_project:
                    raise httpx.ConnectError("simulated failure")
                return httpx.Response(
                    200,
                    json={
                        "bullet_points": [f"Generated bullet for {evidence_id}."],
                    },
                )
            raise AssertionError(f"unexpected endpoint: {endpoint}")

    monkeypatch.setattr("resume_generation.selection.httpx.Client", FakeClient)
    monkeypatch.setattr("resume_generation.bullet_points.httpx.Client", FakeClient)
    monkeypatch.setattr(
        "resume_generation.main.load_registered_evidence",
        lambda paths=None: loaded_evidence,
    )

    with pytest.raises(
        ResumeGenerationError,
        match="HTTP request to /generate-bulletpoints failed",
    ):
        run_resume_generation_pipeline(
            config_path=config_path,
            job_target_path=job_path,
            evidence_paths={
                "projects": projects_path,
                "skills": skills_path,
            },
        )

    fail_second_project = False
    run_resume_generation_pipeline(
        config_path=config_path,
        job_target_path=job_path,
        evidence_paths={
            "projects": projects_path,
            "skills": skills_path,
        },
    )

    assert calls == [
        ("/select-skills", None),
        ("/select-projects", None),
        ("/generate-bulletpoints", "active-project"),
        ("/generate-bulletpoints", "second-project"),
        ("/generate-bulletpoints", "second-project"),
        ("/generate-bulletpoints", "backend-engineer"),
    ]


def test_resume_generation_pipeline_optionally_scans_links_before_bullet_generation(
    monkeypatch,
    tmp_path,
):
    config_path = _write_yaml(
        tmp_path / "config.yaml",
        _config_payload(
            link_scanning={
                "enabled": True,
                "dev_mode": True,
                "llm_model": "link-model",
                "llm_max_output_tokens": 660,
            }
        ),
    )
    job_path = _write_yaml(tmp_path / "job.yaml", _job_target_payload())
    projects_path = _write_yaml(tmp_path / "projects.yaml", _projects_payload())
    skills_path = _write_yaml(tmp_path / "skills.yaml", _skills_payload())
    loaded_evidence = _loaded_evidence(projects_path, skills_path)
    calls: list[str] = []
    bullet_payloads: list[dict] = []

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
            if endpoint == "/scan-link":
                return httpx.Response(
                    200,
                    json={
                        "project_id": json["project"]["id"],
                        "added_highlights": [
                            {
                                "text": "Scanned link confirms project context.",
                                "source_url": "https://example.com/active",
                            }
                        ],
                    },
                )
            if endpoint == "/generate-bulletpoints":
                bullet_payloads.append(json)
                evidence = json.get("project") or json.get("experience")
                return httpx.Response(
                    200,
                    json={
                        "bullet_points": [f"Generated bullet for {evidence['id']}."],
                    },
                )
            raise AssertionError(f"unexpected endpoint: {endpoint}")

    monkeypatch.setattr("resume_generation.selection.httpx.Client", FakeClient)
    monkeypatch.setattr("resume_generation.link_scanning.httpx.Client", FakeClient)
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

    assert calls == [
        "/select-skills",
        "/select-projects",
        "/scan-link",
        "/generate-bulletpoints",
        "/generate-bulletpoints",
    ]
    assert bullet_payloads[0]["project"]["highlights"] == [
        "Built the service.",
        "Scanned link confirms project context.",
    ]
    assert bullet_payloads[0]["project"]["skills"]["technology"] == ["FastAPI"]
    assert bullet_payloads[1]["experience"]["id"] == "backend-engineer"
    assert result.projects[0].bullet_points == ["Generated bullet for active-project."]


def api_request(method: str, path: str, **kwargs):
    async def _request():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(_request())


def test_generate_bulletpoints_route_logs_http_source(monkeypatch, caplog):
    monkeypatch.setattr(
        "app.main.generate_bulletpoints_service",
        lambda payload: BulletGenerationResponse(bullet_points=["Built APIs."]),
    )

    with caplog.at_level(logging.INFO, logger="app_main"):
        response = api_request(
            "POST",
            "/generate-bulletpoints",
            json={
                "context": {
                    "title": "Backend Engineer",
                    "description": "Build APIs.",
                },
                "project": _projects_payload()["projects"][0],
            },
        )

    assert response.status_code == 200
    route_records = [
        record
        for record in caplog.records
        if getattr(record, "event", None) == "app_content_stage_request"
    ]
    assert len(route_records) == 1
    record = route_records[0]
    assert record.stage == "project_bullet_points"
    assert record.endpoint == "/generate-bulletpoints"
    assert record.source == "http"
    assert record.evidence_type == "project"
    assert record.evidence_id == "active-project"


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
