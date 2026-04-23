from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from app.resume_evidence.loader import DEFAULT_EVIDENCE_PATHS, load_evidence_yaml
from app.resume_evidence.models import ProjectRecord, ProjectsFile


def _projects_file_to_data(projects_file: ProjectsFile) -> dict[str, Any]:
    return projects_file.model_dump(mode="python")


def _normalize_slug_text(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "project"


def generate_project_id(name: str, existing_ids: set[str]) -> str:
    base_slug = _normalize_slug_text(name)
    candidate = base_slug
    suffix = 2

    while candidate in existing_ids:
        candidate = f"{base_slug}-{suffix}"
        suffix += 1

    return candidate


@dataclass(frozen=True)
class PendingProjectChanges:
    created: tuple[str, ...]
    updated: tuple[str, ...]
    deleted: tuple[str, ...]

    def is_empty(self) -> bool:
        return not (self.created or self.updated or self.deleted)


class ProjectsEvidenceSession:
    def __init__(self, path: Path, baseline: ProjectsFile):
        self.path = path
        self._baseline = baseline
        self._staged = baseline.model_copy(deep=True)

    @classmethod
    def load(cls, path: Path | str | None = None) -> "ProjectsEvidenceSession":
        resolved_path = Path(path) if path is not None else DEFAULT_EVIDENCE_PATHS["projects"]
        loaded = load_evidence_yaml(resolved_path, "projects")
        if not isinstance(loaded, ProjectsFile):
            raise TypeError("Expected projects evidence to load into ProjectsFile")
        return cls(resolved_path, loaded)

    @property
    def baseline(self) -> ProjectsFile:
        return self._baseline.model_copy(deep=True)

    @property
    def staged(self) -> ProjectsFile:
        return self._staged.model_copy(deep=True)

    @property
    def dirty(self) -> bool:
        return _projects_file_to_data(self._baseline) != _projects_file_to_data(self._staged)

    def list_projects(self) -> list[ProjectRecord]:
        return list(self._staged.projects)

    def get_project(self, index: int) -> ProjectRecord:
        return self._staged.projects[self._resolve_index(index)].model_copy(deep=True)

    def create_project(
        self,
        *,
        name: str,
        summary: str,
        highlights: list[str],
        active: bool,
        technology: list[str],
        programming: list[str],
        concepts: list[str],
        links: list[str] | None,
    ) -> ProjectRecord:
        staged_data = _projects_file_to_data(self._staged)
        existing_ids = {project["id"] for project in staged_data["projects"]}
        project_data = {
            "id": generate_project_id(name, existing_ids),
            "name": name,
            "summary": summary,
            "highlights": highlights,
            "active": active,
            "skills": {
                "technology": technology,
                "programming": programming,
                "concepts": concepts,
            },
            "links": links,
        }
        staged_data["projects"].append(project_data)
        validated = self._validate_projects_file(staged_data)
        self._staged = validated
        return validated.projects[-1].model_copy(deep=True)

    def update_project(
        self,
        index: int,
        *,
        name: str,
        summary: str,
        highlights: list[str],
        active: bool,
        technology: list[str],
        programming: list[str],
        concepts: list[str],
        links: list[str] | None,
    ) -> ProjectRecord:
        staged_data = _projects_file_to_data(self._staged)
        resolved_index = self._resolve_index(index)
        original_project = staged_data["projects"][resolved_index]
        staged_data["projects"][resolved_index] = {
            "id": original_project["id"],
            "name": name,
            "summary": summary,
            "highlights": highlights,
            "active": active,
            "skills": {
                "technology": technology,
                "programming": programming,
                "concepts": concepts,
            },
            "links": links,
        }
        validated = self._validate_projects_file(staged_data)
        self._staged = validated
        return validated.projects[resolved_index].model_copy(deep=True)

    def delete_project(self, index: int) -> ProjectRecord:
        staged_data = _projects_file_to_data(self._staged)
        resolved_index = self._resolve_index(index)
        deleted_project = staged_data["projects"].pop(resolved_index)
        validated = self._validate_projects_file(staged_data)
        self._staged = validated
        return ProjectRecord.model_validate(deleted_project)

    def reload(self) -> None:
        reloaded = load_evidence_yaml(self.path, "projects")
        if not isinstance(reloaded, ProjectsFile):
            raise TypeError("Expected projects evidence to reload into ProjectsFile")
        self._baseline = reloaded
        self._staged = reloaded.model_copy(deep=True)

    def apply(self) -> None:
        staged_data = _projects_file_to_data(self._staged)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_file_path: str | None = None

        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                yaml.safe_dump(staged_data, handle, sort_keys=False)
                temp_file_path = handle.name

            if temp_file_path is None:
                raise RuntimeError("Failed to create temporary file for projects evidence save")

            os.replace(temp_file_path, self.path)
        finally:
            if temp_file_path is not None and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

        self._baseline = self._staged.model_copy(deep=True)

    def pending_changes(self) -> PendingProjectChanges:
        baseline_projects = {project.id: project for project in self._baseline.projects}
        staged_projects = {project.id: project for project in self._staged.projects}

        created = tuple(
            staged_projects[project_id].name
            for project_id in staged_projects
            if project_id not in baseline_projects
        )
        deleted = tuple(
            baseline_projects[project_id].name
            for project_id in baseline_projects
            if project_id not in staged_projects
        )
        updated = tuple(
            staged_projects[project_id].name
            for project_id in staged_projects
            if project_id in baseline_projects
            and staged_projects[project_id].model_dump(mode="python")
            != baseline_projects[project_id].model_dump(mode="python")
        )

        return PendingProjectChanges(created=created, updated=updated, deleted=deleted)

    def _resolve_index(self, index: int) -> int:
        if index < 1 or index > len(self._staged.projects):
            raise IndexError(f"Project index {index} is out of range")
        return index - 1

    def _validate_projects_file(self, data: dict[str, Any]) -> ProjectsFile:
        try:
            return ProjectsFile.model_validate(data)
        except ValidationError as exc:
            raise ValueError(str(exc)) from exc
