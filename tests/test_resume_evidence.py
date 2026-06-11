from __future__ import annotations

import asyncio
from copy import deepcopy

import pytest
import resume_evidence
import yaml
from pydantic import ValidationError

from app.main import app, lifespan
from resume_evidence import (
    DEFAULT_EVIDENCE_PATHS,
    EducationFile,
    EducationRecord,
    ProjectRecord,
    ProjectsFile,
    SkillsFile,
    UserInfoFile,
    load_evidence_yaml,
    load_registered_evidence,
)


def test_resume_evidence_package_is_top_level():
    assert "/resume_evidence/" in str(resume_evidence.__file__)
    assert "/app/resume_evidence/" not in str(resume_evidence.__file__)


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


def _valid_skills_payload() -> dict:
    return {
        "schema_version": 1,
        "skills": {
            "technology": ["FastAPI", "OpenAI"],
            "programming": ["Python"],
            "concepts": ["Schema validation"],
        },
    }


def _valid_user_payload() -> dict:
    return {
        "schema_version": 1,
        "name": "Example Candidate",
        "email": "candidate@example.com",
        "phone": "+1 555-0100",
        "linkedin": "https://www.linkedin.com/in/example-candidate",
        "github": "https://github.com/example-candidate",
    }


def _valid_education_payload() -> dict:
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
                "relevant_coursework": [
                    "Data Structures",
                    "Algorithms",
                    "Software Engineering",
                ],
            }
        ],
    }


def test_load_projects_yaml_returns_typed_runtime_object(tmp_path):
    path = _write_yaml(tmp_path, _valid_projects_payload())

    parsed = load_evidence_yaml(path, "projects")

    assert isinstance(parsed, ProjectsFile)
    assert isinstance(parsed.projects[0], ProjectRecord)
    assert parsed.schema_version == 1
    assert [project.id for project in parsed.iter_projects()] == ["jobforge"]
    assert parsed.projects_by_id()["jobforge"].name == "JobForge"


def test_load_skills_yaml_returns_typed_runtime_object(tmp_path):
    path = _write_yaml(tmp_path, _valid_skills_payload(), filename="skills.yaml")

    parsed = load_evidence_yaml(path, "skills")

    assert isinstance(parsed, SkillsFile)
    assert parsed.schema_version == 1
    assert parsed.skills.technology == ["FastAPI", "OpenAI"]


def test_load_user_yaml_returns_typed_runtime_object(tmp_path):
    path = _write_yaml(tmp_path, _valid_user_payload(), filename="user.yaml")

    parsed = load_evidence_yaml(path, "user")

    assert isinstance(parsed, UserInfoFile)
    assert parsed.schema_version == 1
    assert parsed.name == "Example Candidate"
    assert parsed.linkedin == "https://www.linkedin.com/in/example-candidate"


def test_load_education_yaml_returns_typed_runtime_object(tmp_path):
    path = _write_yaml(tmp_path, _valid_education_payload(), filename="education.yaml")

    parsed = load_evidence_yaml(path, "education")

    assert isinstance(parsed, EducationFile)
    assert isinstance(parsed.education[0], EducationRecord)
    assert parsed.schema_version == 1
    assert parsed.education[0].name == "Example University"
    assert parsed.education[0].relevant_coursework == [
        "Data Structures",
        "Algorithms",
        "Software Engineering",
    ]


def test_load_projects_yaml_rejects_missing_required_field(tmp_path):
    payload = _valid_projects_payload()
    del payload["projects"][0]["summary"]
    path = _write_yaml(tmp_path, payload)

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "projects")

    assert "summary" in str(exc_info.value)


def test_load_skills_yaml_rejects_missing_required_field(tmp_path):
    payload = _valid_skills_payload()
    del payload["skills"]["concepts"]
    path = _write_yaml(tmp_path, payload, filename="skills.yaml")

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "skills")

    assert "concepts" in str(exc_info.value)


def test_load_user_yaml_rejects_missing_required_field(tmp_path):
    payload = _valid_user_payload()
    del payload["email"]
    path = _write_yaml(tmp_path, payload, filename="user.yaml")

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "user")

    assert "email" in str(exc_info.value)


@pytest.mark.parametrize(
    "field_name",
    ["name", "degree", "grade", "start", "location", "relevant_coursework"],
)
def test_load_education_yaml_rejects_missing_required_field(tmp_path, field_name):
    payload = _valid_education_payload()
    del payload["education"][0][field_name]
    path = _write_yaml(tmp_path, payload, filename="education.yaml")

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "education")

    assert field_name in str(exc_info.value)


def test_load_education_yaml_accepts_missing_optional_end(tmp_path):
    payload = _valid_education_payload()
    del payload["education"][0]["end"]
    path = _write_yaml(tmp_path, payload, filename="education.yaml")

    parsed = load_evidence_yaml(path, "education")

    assert isinstance(parsed, EducationFile)
    assert parsed.education[0].end is None


def test_load_projects_yaml_rejects_extra_top_level_field(tmp_path):
    payload = _valid_projects_payload()
    payload["unexpected"] = "nope"
    path = _write_yaml(tmp_path, payload)

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "projects")

    assert "unexpected" in str(exc_info.value)


def test_load_skills_yaml_rejects_extra_top_level_field(tmp_path):
    payload = _valid_skills_payload()
    payload["unexpected"] = "nope"
    path = _write_yaml(tmp_path, payload, filename="skills.yaml")

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "skills")

    assert "unexpected" in str(exc_info.value)


def test_load_user_yaml_rejects_extra_top_level_field(tmp_path):
    payload = _valid_user_payload()
    payload["unexpected"] = "nope"
    path = _write_yaml(tmp_path, payload, filename="user.yaml")

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "user")

    assert "unexpected" in str(exc_info.value)


def test_load_education_yaml_rejects_extra_top_level_field(tmp_path):
    payload = _valid_education_payload()
    payload["unexpected"] = "nope"
    path = _write_yaml(tmp_path, payload, filename="education.yaml")

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "education")

    assert "unexpected" in str(exc_info.value)


def test_load_projects_yaml_rejects_extra_project_field(tmp_path):
    payload = _valid_projects_payload()
    payload["projects"][0]["extra_field"] = "nope"
    path = _write_yaml(tmp_path, payload)

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "projects")

    assert "extra_field" in str(exc_info.value)


def test_load_education_yaml_rejects_extra_record_field(tmp_path):
    payload = _valid_education_payload()
    payload["education"][0]["extra_field"] = "nope"
    path = _write_yaml(tmp_path, payload, filename="education.yaml")

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "education")

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


def test_load_skills_yaml_rejects_extra_skill_category(tmp_path):
    payload = _valid_skills_payload()
    payload["skills"]["other"] = []
    path = _write_yaml(tmp_path, payload, filename="skills.yaml")

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "skills")

    assert "other" in str(exc_info.value)


def test_load_projects_yaml_rejects_non_list_skill_bucket(tmp_path):
    payload = _valid_projects_payload()
    payload["projects"][0]["skills"]["technology"] = "FastAPI"
    path = _write_yaml(tmp_path, payload)

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "projects")

    assert "technology" in str(exc_info.value)


def test_load_skills_yaml_rejects_non_list_skill_bucket(tmp_path):
    payload = _valid_skills_payload()
    payload["skills"]["technology"] = "FastAPI"
    path = _write_yaml(tmp_path, payload, filename="skills.yaml")

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "skills")

    assert "technology" in str(exc_info.value)


def test_load_projects_yaml_rejects_unsupported_schema_version(tmp_path):
    payload = _valid_projects_payload()
    payload["schema_version"] = 2
    path = _write_yaml(tmp_path, payload)

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "projects")

    assert "schema_version" in str(exc_info.value)


def test_load_skills_yaml_rejects_unsupported_schema_version(tmp_path):
    payload = _valid_skills_payload()
    payload["schema_version"] = 2
    path = _write_yaml(tmp_path, payload, filename="skills.yaml")

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "skills")

    assert "schema_version" in str(exc_info.value)


def test_load_user_yaml_rejects_unsupported_schema_version(tmp_path):
    payload = _valid_user_payload()
    payload["schema_version"] = 2
    path = _write_yaml(tmp_path, payload, filename="user.yaml")

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "user")

    assert "schema_version" in str(exc_info.value)


def test_load_education_yaml_rejects_unsupported_schema_version(tmp_path):
    payload = _valid_education_payload()
    payload["schema_version"] = 2
    path = _write_yaml(tmp_path, payload, filename="education.yaml")

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "education")

    assert "schema_version" in str(exc_info.value)


@pytest.mark.parametrize("field_name", ["name", "email", "phone"])
def test_load_user_yaml_rejects_empty_required_strings(tmp_path, field_name):
    payload = _valid_user_payload()
    payload[field_name] = "   "
    path = _write_yaml(tmp_path, payload, filename="user.yaml")

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "user")

    assert field_name in str(exc_info.value)


@pytest.mark.parametrize("field_name", ["linkedin", "github"])
def test_load_user_yaml_rejects_empty_optional_links_when_provided(tmp_path, field_name):
    payload = _valid_user_payload()
    payload[field_name] = "   "
    path = _write_yaml(tmp_path, payload, filename="user.yaml")

    with pytest.raises(ValidationError) as exc_info:
        load_evidence_yaml(path, "user")

    assert field_name in str(exc_info.value)


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
    projects_path = _write_yaml(tmp_path, _valid_projects_payload())
    skills_path = _write_yaml(tmp_path, _valid_skills_payload(), filename="skills.yaml")
    user_path = _write_yaml(tmp_path, _valid_user_payload(), filename="user.yaml")
    education_path = _write_yaml(tmp_path, _valid_education_payload(), filename="education.yaml")

    loaded = load_registered_evidence(
        {
            "education": education_path,
            "projects": projects_path,
            "skills": skills_path,
            "user": user_path,
        }
    )

    assert isinstance(loaded["education"], EducationFile)
    assert isinstance(loaded["projects"], ProjectsFile)
    assert isinstance(loaded["skills"], SkillsFile)
    assert isinstance(loaded["user"], UserInfoFile)
    assert loaded["education"].education[0].degree.startswith("Bachelor")
    assert loaded["projects"].projects_by_id()["jobforge"].summary.startswith("Grounded resume")
    assert loaded["skills"].skills.programming == ["Python"]
    assert loaded["user"].email == "candidate@example.com"


def test_default_evidence_path_points_to_user_directory():
    assert str(DEFAULT_EVIDENCE_PATHS["education"]).endswith(
        "user/resume_evidence/education.yaml"
    )
    assert str(DEFAULT_EVIDENCE_PATHS["projects"]).endswith("user/resume_evidence/projects.yaml")
    assert str(DEFAULT_EVIDENCE_PATHS["skills"]).endswith("user/resume_evidence/skills.yaml")
    assert str(DEFAULT_EVIDENCE_PATHS["user"]).endswith("user/resume_evidence/user.yaml")


def test_app_startup_loads_resume_evidence(monkeypatch):
    loaded = {
        "education": EducationFile.model_validate(_valid_education_payload()),
        "projects": ProjectsFile.model_validate(_valid_projects_payload()),
        "skills": SkillsFile.model_validate(_valid_skills_payload()),
        "user": UserInfoFile.model_validate(_valid_user_payload()),
    }

    monkeypatch.setattr("app.main.load_registered_evidence", lambda: loaded)

    async def _run_startup():
        async with lifespan(app):
            assert app.state.resume_evidence == loaded

    asyncio.run(_run_startup())
