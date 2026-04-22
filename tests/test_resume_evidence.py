from __future__ import annotations

import asyncio
from copy import deepcopy

import pytest
import yaml
from pydantic import ValidationError

from app.main import app, lifespan
from app.resume_evidence import (
    DEFAULT_EVIDENCE_PATHS,
    ProjectRecord,
    ProjectsFile,
    load_evidence_yaml,
    load_registered_evidence,
)


def _valid_projects_payload() -> dict:
    return {
        "schema_version": 1,
        "projects": [
            {
                "id": "jobforge",
                "name": "JobForge",
                "summary": "Grounded resume tooling for deterministic resume generation.",
                "highlights": [
                    "Built a deterministic baseline skill selector.",
                    "Defined a file-based evidence pipeline for resume generation.",
                ],
                "active": True,
                "skills": {
                    "technology": ["FastAPI", "OpenAI"],
                    "programming": ["Python"],
                    "concepts": ["Deterministic systems", "Schema validation"],
                },
                "links": [
                    "https://github.com/example/jobforge",
                    "https://jobforge.example.com",
                ],
            }
        ],
    }


def _write_yaml(tmp_path, payload: dict, filename: str = "projects.yaml"):
    path = tmp_path / filename
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def test_load_projects_yaml_returns_typed_runtime_object(tmp_path):
    path = _write_yaml(tmp_path, _valid_projects_payload())

    parsed = load_evidence_yaml(path, "projects")

    assert isinstance(parsed, ProjectsFile)
    assert isinstance(parsed.projects[0], ProjectRecord)
    assert parsed.schema_version == 1
    assert [project.id for project in parsed.iter_projects()] == ["jobforge"]
    assert parsed.projects_by_id()["jobforge"].name == "JobForge"


def test_load_projects_yaml_rejects_missing_required_field(tmp_path):
    payload = _valid_projects_payload()
    del payload["projects"][0]["summary"]
    path = _write_yaml(tmp_path, payload)

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "projects")

    assert "summary" in str(exc_info.value)


def test_load_projects_yaml_rejects_extra_top_level_field(tmp_path):
    payload = _valid_projects_payload()
    payload["unexpected"] = "nope"
    path = _write_yaml(tmp_path, payload)

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "projects")

    assert "unexpected" in str(exc_info.value)


def test_load_projects_yaml_rejects_extra_project_field(tmp_path):
    payload = _valid_projects_payload()
    payload["projects"][0]["extra_field"] = "nope"
    path = _write_yaml(tmp_path, payload)

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "projects")

    assert "extra_field" in str(exc_info.value)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("active", "true"),
        ("highlights", "not-a-list"),
        ("skills", ["not", "a", "mapping"]),
        ("links", [123]),
    ],
)
def test_load_projects_yaml_rejects_wrong_project_field_types(tmp_path, field_name, value):
    payload = _valid_projects_payload()
    payload["projects"][0][field_name] = value
    path = _write_yaml(tmp_path, payload)

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "projects")

    assert field_name in str(exc_info.value)


def test_load_projects_yaml_rejects_empty_highlights(tmp_path):
    payload = _valid_projects_payload()
    payload["projects"][0]["highlights"] = []
    path = _write_yaml(tmp_path, payload)

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "projects")

    assert "highlights" in str(exc_info.value)


def test_load_projects_yaml_rejects_missing_skill_category(tmp_path):
    payload = _valid_projects_payload()
    del payload["projects"][0]["skills"]["concepts"]
    path = _write_yaml(tmp_path, payload)

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "projects")

    assert "concepts" in str(exc_info.value)


def test_load_projects_yaml_rejects_extra_skill_category(tmp_path):
    payload = _valid_projects_payload()
    payload["projects"][0]["skills"]["other"] = []
    path = _write_yaml(tmp_path, payload)

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "projects")

    assert "other" in str(exc_info.value)


def test_load_projects_yaml_rejects_non_list_skill_bucket(tmp_path):
    payload = _valid_projects_payload()
    payload["projects"][0]["skills"]["technology"] = "FastAPI"
    path = _write_yaml(tmp_path, payload)

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "projects")

    assert "technology" in str(exc_info.value)


def test_load_projects_yaml_rejects_unsupported_schema_version(tmp_path):
    payload = _valid_projects_payload()
    payload["schema_version"] = 2
    path = _write_yaml(tmp_path, payload)

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "projects")

    assert "schema_version" in str(exc_info.value)


def test_load_projects_yaml_rejects_duplicate_project_ids(tmp_path):
    payload = _valid_projects_payload()
    duplicate = deepcopy(payload["projects"][0])
    duplicate["name"] = "JobForge Clone"
    payload["projects"].append(duplicate)
    path = _write_yaml(tmp_path, payload)

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "projects")

    assert "Duplicate project ids are not allowed: jobforge" in str(exc_info.value)


def test_load_evidence_yaml_rejects_unknown_schema_name(tmp_path):
    path = _write_yaml(tmp_path, _valid_projects_payload())

    with pytest.raises(ValueError) as exc_info:
        load_evidence_yaml(path, "unknown")

    assert "Unsupported evidence schema 'unknown'" in str(exc_info.value)


def test_load_projects_yaml_is_deterministic_across_repeated_parses(tmp_path):
    path = _write_yaml(tmp_path, _valid_projects_payload())

    first = load_evidence_yaml(path, "projects")
    second = load_evidence_yaml(path, "projects")

    assert first.model_dump() == second.model_dump()


def test_load_registered_evidence_loads_registered_schemas(tmp_path):
    path = _write_yaml(tmp_path, _valid_projects_payload())

    loaded = load_registered_evidence({"projects": path})

    assert isinstance(loaded["projects"], ProjectsFile)
    assert loaded["projects"].projects_by_id()["jobforge"].summary.startswith("Grounded resume")


def test_default_evidence_path_points_to_user_directory():
    assert str(DEFAULT_EVIDENCE_PATHS["projects"]).endswith("user/resume_evidence/projects.yaml")


def test_app_startup_loads_resume_evidence(monkeypatch):
    loaded = {"projects": ProjectsFile.model_validate(_valid_projects_payload())}

    monkeypatch.setattr("app.main.load_registered_evidence", lambda: loaded)

    async def _run_startup():
        async with lifespan(app):
            assert app.state.resume_evidence == loaded

    asyncio.run(_run_startup())
