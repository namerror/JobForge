from __future__ import annotations

from io import StringIO

import pytest
import yaml

from app.resume_evidence import ProjectsEvidenceSession, load_evidence_yaml
from app.resume_evidence.cli import main as cli_main
from app.resume_evidence.session import generate_project_id


def _valid_projects_payload() -> dict:
    return {
        "schema_version": 1,
        "projects": [
            {
                "id": "project-123",
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
                ],
            }
        ],
    }


def _write_yaml(tmp_path, payload: dict, filename: str = "projects.yaml"):
    path = tmp_path / filename
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


class InputFeeder:
    def __init__(self, responses: list[str]):
        self._responses = iter(responses)

    def __call__(self, _prompt: str) -> str:
        try:
            return next(self._responses)
        except StopIteration as exc:
            raise EOFError from exc


def _run_cli(path, responses: list[str]) -> str:
    output = StringIO()
    exit_code = cli_main(["--path", str(path)], input_func=InputFeeder(responses), output=output)
    assert exit_code == 0
    return output.getvalue()


def test_generate_project_id_adds_numeric_suffix_for_duplicates():
    existing_ids = {"jobforge", "jobforge-2"}

    assert generate_project_id("JobForge", existing_ids) == "jobforge-3"


def test_session_create_stages_changes_without_writing_file(tmp_path):
    path = _write_yaml(tmp_path, _valid_projects_payload())
    session = ProjectsEvidenceSession.load(path)

    created = session.create_project(
        name="Portfolio Tracker",
        summary="Tracks resume-ready work samples.",
        highlights=["Built CRUD workflows for resume evidence."],
        active=True,
        technology=["FastAPI"],
        programming=["Python"],
        concepts=["CLI design"],
        links=None,
    )

    assert created.id == "portfolio-tracker"
    assert session.dirty is True
    loaded = load_evidence_yaml(path, "projects")
    assert loaded.model_dump()["projects"] == _valid_projects_payload()["projects"]


def test_session_update_keeps_original_id_on_rename(tmp_path):
    path = _write_yaml(tmp_path, _valid_projects_payload())
    session = ProjectsEvidenceSession.load(path)

    updated = session.update_project(
        1,
        name="JobForge CLI",
        summary="Updated summary",
        highlights=["Built a deterministic baseline skill selector."],
        active=True,
        technology=["FastAPI"],
        programming=["Python"],
        concepts=["Schema validation"],
        links=["https://github.com/example/jobforge"],
    )

    assert updated.id == "project-123"
    assert updated.name == "JobForge CLI"


def test_session_delete_removes_project_from_staged_state(tmp_path):
    path = _write_yaml(tmp_path, _valid_projects_payload())
    session = ProjectsEvidenceSession.load(path)

    deleted = session.delete_project(1)

    assert deleted.name == "JobForge"
    assert session.list_projects() == []


def test_session_rejects_invalid_edit_without_mutating_staged_state(tmp_path):
    path = _write_yaml(tmp_path, _valid_projects_payload())
    session = ProjectsEvidenceSession.load(path)
    before = session.staged.model_dump()

    with pytest.raises(ValueError):
        session.update_project(
            1,
            name="JobForge",
            summary="Updated summary",
            highlights=[],
            active=True,
            technology=["FastAPI"],
            programming=["Python"],
            concepts=["Schema validation"],
            links=None,
        )

    assert session.staged.model_dump() == before


def test_session_apply_writes_schema_valid_yaml_and_clears_dirty_flag(tmp_path):
    path = _write_yaml(tmp_path, _valid_projects_payload())
    session = ProjectsEvidenceSession.load(path)

    session.create_project(
        name="Portfolio Tracker",
        summary="Tracks resume-ready work samples.",
        highlights=["Built CRUD workflows for resume evidence."],
        active=True,
        technology=["FastAPI"],
        programming=["Python"],
        concepts=["CLI design"],
        links=["https://example.com/portfolio-tracker"],
    )

    session.apply()

    reloaded = load_evidence_yaml(path, "projects")
    assert reloaded.schema_version == 1
    assert [project.name for project in reloaded.projects] == ["JobForge", "Portfolio Tracker"]
    assert session.dirty is False


def test_cli_list_shows_numbered_projects(tmp_path):
    path = _write_yaml(tmp_path, _valid_projects_payload())

    output = _run_cli(path, ["list", "quit"])

    assert "1. JobForge [active]" in output


def test_cli_create_stages_changes_without_persisting_before_apply(tmp_path):
    path = _write_yaml(tmp_path, _valid_projects_payload())

    output = _run_cli(
        path,
        [
            "create",
            "Portfolio Tracker",
            "Tracks resume-ready work samples.",
            "Built CRUD workflows for resume evidence.",
            "",
            "",
            "FastAPI",
            "",
            "",
            "",
            "",
            "quit",
            "y",
        ],
    )

    loaded = load_evidence_yaml(path, "projects")
    assert [project.name for project in loaded.projects] == ["JobForge"]
    assert "Run 'apply' to save." in output


def test_cli_edit_updates_project_after_apply_and_keeps_id_hidden(tmp_path):
    path = _write_yaml(tmp_path, _valid_projects_payload())

    output = _run_cli(
        path,
        [
            "edit 1",
            "",
            "Updated summary",
            "y",
            "",
            "y",
            "y",
            "y",
            "y",
            "apply",
            "y",
            "show 1",
            "quit",
        ],
    )

    loaded = load_evidence_yaml(path, "projects")
    assert loaded.projects[0].summary == "Updated summary"
    assert loaded.projects[0].id == "project-123"
    assert "project-123" not in output


def test_cli_apply_requires_confirmation_before_writing(tmp_path):
    path = _write_yaml(tmp_path, _valid_projects_payload())

    output = _run_cli(
        path,
        [
            "create",
            "Portfolio Tracker",
            "Tracks resume-ready work samples.",
            "Built CRUD workflows for resume evidence.",
            "",
            "",
            "",
            "",
            "",
            "",
            "apply",
            "n",
            "quit",
            "y",
        ],
    )

    loaded = load_evidence_yaml(path, "projects")
    assert [project.name for project in loaded.projects] == ["JobForge"]
    assert "Apply canceled." in output


def test_cli_reload_discards_dirty_changes_only_after_confirmation(tmp_path):
    path = _write_yaml(tmp_path, _valid_projects_payload())

    output = _run_cli(
        path,
        [
            "create",
            "Portfolio Tracker",
            "Tracks resume-ready work samples.",
            "Built CRUD workflows for resume evidence.",
            "",
            "",
            "",
            "",
            "",
            "",
            "reload",
            "y",
            "list",
            "quit",
        ],
    )

    loaded = load_evidence_yaml(path, "projects")
    assert [project.name for project in loaded.projects] == ["JobForge"]
    assert "Portfolio Tracker" not in output.split("Reloaded projects evidence from disk.")[-1]


def test_cli_quit_warns_about_unapplied_changes(tmp_path):
    path = _write_yaml(tmp_path, _valid_projects_payload())

    output = _run_cli(
        path,
        [
            "create",
            "Portfolio Tracker",
            "Tracks resume-ready work samples.",
            "Built CRUD workflows for resume evidence.",
            "",
            "",
            "",
            "",
            "",
            "",
            "quit",
            "n",
            "quit",
            "y",
        ],
    )

    assert "Quit canceled." in output
