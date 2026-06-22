from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from resume_evidence.loader import DEFAULT_EVIDENCE_PATHS, load_evidence_yaml
from resume_evidence.models import (
    EducationFile,
    EducationRecord,
    ExperienceFile,
    ExperienceRecord,
    ProjectRecord,
    ProjectsFile,
    SkillsFile,
    UserInfoFile,
)


def _projects_file_to_data(projects_file: ProjectsFile) -> dict[str, Any]:
    return projects_file.model_dump(mode="python")


def _skills_file_to_data(skills_file: SkillsFile) -> dict[str, Any]:
    return skills_file.model_dump(mode="python")


def _education_file_to_data(education_file: EducationFile) -> dict[str, Any]:
    return education_file.model_dump(mode="python")


def _experience_file_to_data(experience_file: ExperienceFile) -> dict[str, Any]:
    return experience_file.model_dump(mode="python")


def _user_info_file_to_data(user_info_file: UserInfoFile) -> dict[str, Any]:
    return user_info_file.model_dump(mode="python")


def _normalize_slug_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def generate_record_id(name: str, existing_ids: set[str], fallback: str) -> str:
    base_slug = _normalize_slug_text(name) or fallback
    candidate = base_slug
    suffix = 2

    while candidate in existing_ids:
        candidate = f"{base_slug}-{suffix}"
        suffix += 1

    return candidate


def generate_project_id(name: str, existing_ids: set[str]) -> str:
    return generate_record_id(name, existing_ids, "project")


def generate_experience_id(name: str, existing_ids: set[str]) -> str:
    return generate_record_id(name, existing_ids, "experience")


@dataclass(frozen=True)
class PendingProjectChanges:
    created: tuple[str, ...]
    updated: tuple[str, ...]
    deleted: tuple[str, ...]

    def is_empty(self) -> bool:
        return not (self.created or self.updated or self.deleted)


@dataclass(frozen=True)
class PendingSkillsChanges:
    changed_categories: tuple[str, ...]

    def is_empty(self) -> bool:
        return not self.changed_categories


@dataclass(frozen=True)
class PendingEducationChanges:
    created: tuple[str, ...]
    updated: tuple[str, ...]
    deleted: tuple[str, ...]

    def is_empty(self) -> bool:
        return not (self.created or self.updated or self.deleted)


@dataclass(frozen=True)
class PendingExperienceChanges:
    created: tuple[str, ...]
    updated: tuple[str, ...]
    deleted: tuple[str, ...]

    def is_empty(self) -> bool:
        return not (self.created or self.updated or self.deleted)


@dataclass(frozen=True)
class PendingUserInfoChanges:
    changed_fields: tuple[str, ...]

    def is_empty(self) -> bool:
        return not self.changed_fields


def _write_yaml_atomic(path: Path, data: dict[str, Any], error_context: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_file_path: str | None = None

    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            yaml.safe_dump(data, handle, sort_keys=False)
            temp_file_path = handle.name

        if temp_file_path is None:
            raise RuntimeError(f"Failed to create temporary file for {error_context}")

        os.replace(temp_file_path, path)
    finally:
        if temp_file_path is not None and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


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
        _write_yaml_atomic(self.path, staged_data, "projects evidence save")
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


class EducationEvidenceSession:
    def __init__(self, path: Path, baseline: EducationFile):
        self.path = path
        self._baseline = baseline
        self._staged = baseline.model_copy(deep=True)

    @classmethod
    def load(cls, path: Path | str | None = None) -> "EducationEvidenceSession":
        resolved_path = Path(path) if path is not None else DEFAULT_EVIDENCE_PATHS["education"]
        loaded = load_evidence_yaml(resolved_path, "education")
        if not isinstance(loaded, EducationFile):
            raise TypeError("Expected education evidence to load into EducationFile")
        return cls(resolved_path, loaded)

    @property
    def baseline(self) -> EducationFile:
        return self._baseline.model_copy(deep=True)

    @property
    def staged(self) -> EducationFile:
        return self._staged.model_copy(deep=True)

    @property
    def dirty(self) -> bool:
        return _education_file_to_data(self._baseline) != _education_file_to_data(self._staged)

    def list_education(self) -> list[EducationRecord]:
        return list(self._staged.education)

    def get_education(self, index: int) -> EducationRecord:
        return self._staged.education[self._resolve_index(index)].model_copy(deep=True)

    def create_education(
        self,
        *,
        name: str,
        degree: str,
        grade: str,
        start: str,
        end: str | None,
        location: str,
        relevant_coursework: list[str],
    ) -> EducationRecord:
        staged_data = _education_file_to_data(self._staged)
        education_data = {
            "name": name,
            "degree": degree,
            "grade": grade,
            "start": start,
            "end": end,
            "location": location,
            "relevant_coursework": relevant_coursework,
        }
        staged_data["education"].append(education_data)
        validated = self._validate_education_file(staged_data)
        self._staged = validated
        return validated.education[-1].model_copy(deep=True)

    def update_education(
        self,
        index: int,
        *,
        name: str,
        degree: str,
        grade: str,
        start: str,
        end: str | None,
        location: str,
        relevant_coursework: list[str],
    ) -> EducationRecord:
        staged_data = _education_file_to_data(self._staged)
        resolved_index = self._resolve_index(index)
        staged_data["education"][resolved_index] = {
            "name": name,
            "degree": degree,
            "grade": grade,
            "start": start,
            "end": end,
            "location": location,
            "relevant_coursework": relevant_coursework,
        }
        validated = self._validate_education_file(staged_data)
        self._staged = validated
        return validated.education[resolved_index].model_copy(deep=True)

    def delete_education(self, index: int) -> EducationRecord:
        staged_data = _education_file_to_data(self._staged)
        resolved_index = self._resolve_index(index)
        deleted_education = staged_data["education"].pop(resolved_index)
        validated = self._validate_education_file(staged_data)
        self._staged = validated
        return EducationRecord.model_validate(deleted_education)

    def reload(self) -> None:
        reloaded = load_evidence_yaml(self.path, "education")
        if not isinstance(reloaded, EducationFile):
            raise TypeError("Expected education evidence to reload into EducationFile")
        self._baseline = reloaded
        self._staged = reloaded.model_copy(deep=True)

    def apply(self) -> None:
        staged_data = _education_file_to_data(self._staged)
        _write_yaml_atomic(self.path, staged_data, "education evidence save")
        self._baseline = self._staged.model_copy(deep=True)

    def pending_changes(self) -> PendingEducationChanges:
        baseline_education = self._baseline.education
        staged_education = self._staged.education
        common_length = min(len(baseline_education), len(staged_education))

        updated = tuple(
            staged_education[index].name
            for index in range(common_length)
            if staged_education[index].model_dump(mode="python")
            != baseline_education[index].model_dump(mode="python")
        )
        created = tuple(item.name for item in staged_education[common_length:])
        deleted = tuple(item.name for item in baseline_education[common_length:])

        return PendingEducationChanges(created=created, updated=updated, deleted=deleted)

    def _resolve_index(self, index: int) -> int:
        if index < 1 or index > len(self._staged.education):
            raise IndexError(f"Education index {index} is out of range")
        return index - 1

    def _validate_education_file(self, data: dict[str, Any]) -> EducationFile:
        try:
            return EducationFile.model_validate(data)
        except ValidationError as exc:
            raise ValueError(str(exc)) from exc


class ExperienceEvidenceSession:
    def __init__(self, path: Path, baseline: ExperienceFile):
        self.path = path
        self._baseline = baseline
        self._staged = baseline.model_copy(deep=True)

    @classmethod
    def load(cls, path: Path | str | None = None) -> "ExperienceEvidenceSession":
        resolved_path = Path(path) if path is not None else DEFAULT_EVIDENCE_PATHS["experience"]
        loaded = load_evidence_yaml(resolved_path, "experience")
        if not isinstance(loaded, ExperienceFile):
            raise TypeError("Expected experience evidence to load into ExperienceFile")
        return cls(resolved_path, loaded)

    @property
    def baseline(self) -> ExperienceFile:
        return self._baseline.model_copy(deep=True)

    @property
    def staged(self) -> ExperienceFile:
        return self._staged.model_copy(deep=True)

    @property
    def dirty(self) -> bool:
        return _experience_file_to_data(self._baseline) != _experience_file_to_data(self._staged)

    def list_experience(self) -> list[ExperienceRecord]:
        return list(self._staged.experience)

    def get_experience(self, index: int) -> ExperienceRecord:
        return self._staged.experience[self._resolve_index(index)].model_copy(deep=True)

    def create_experience(
        self,
        *,
        name: str,
        role: str,
        summary: str,
        highlights: list[str],
        active: bool,
        technology: list[str],
        programming: list[str],
        concepts: list[str],
        location: str,
        start: str,
        end: str | None,
        links: list[str] | None,
    ) -> ExperienceRecord:
        staged_data = _experience_file_to_data(self._staged)
        existing_ids = {experience["id"] for experience in staged_data["experience"]}
        experience_data = {
            "id": generate_experience_id(name, existing_ids),
            "name": name,
            "role": role,
            "summary": summary,
            "highlights": highlights,
            "active": active,
            "skills": {
                "technology": technology,
                "programming": programming,
                "concepts": concepts,
            },
            "location": location,
            "start": start,
            "end": end,
            "links": links,
        }
        staged_data["experience"].append(experience_data)
        validated = self._validate_experience_file(staged_data)
        self._staged = validated
        return validated.experience[-1].model_copy(deep=True)

    def update_experience(
        self,
        index: int,
        *,
        name: str,
        role: str,
        summary: str,
        highlights: list[str],
        active: bool,
        technology: list[str],
        programming: list[str],
        concepts: list[str],
        location: str,
        start: str,
        end: str | None,
        links: list[str] | None,
    ) -> ExperienceRecord:
        staged_data = _experience_file_to_data(self._staged)
        resolved_index = self._resolve_index(index)
        original_experience = staged_data["experience"][resolved_index]
        staged_data["experience"][resolved_index] = {
            "id": original_experience["id"],
            "name": name,
            "role": role,
            "summary": summary,
            "highlights": highlights,
            "active": active,
            "skills": {
                "technology": technology,
                "programming": programming,
                "concepts": concepts,
            },
            "location": location,
            "start": start,
            "end": end,
            "links": links,
        }
        validated = self._validate_experience_file(staged_data)
        self._staged = validated
        return validated.experience[resolved_index].model_copy(deep=True)

    def delete_experience(self, index: int) -> ExperienceRecord:
        staged_data = _experience_file_to_data(self._staged)
        resolved_index = self._resolve_index(index)
        deleted_experience = staged_data["experience"].pop(resolved_index)
        validated = self._validate_experience_file(staged_data)
        self._staged = validated
        return ExperienceRecord.model_validate(deleted_experience)

    def reload(self) -> None:
        reloaded = load_evidence_yaml(self.path, "experience")
        if not isinstance(reloaded, ExperienceFile):
            raise TypeError("Expected experience evidence to reload into ExperienceFile")
        self._baseline = reloaded
        self._staged = reloaded.model_copy(deep=True)

    def apply(self) -> None:
        staged_data = _experience_file_to_data(self._staged)
        _write_yaml_atomic(self.path, staged_data, "experience evidence save")
        self._baseline = self._staged.model_copy(deep=True)

    def pending_changes(self) -> PendingExperienceChanges:
        baseline_experience = {item.id: item for item in self._baseline.experience}
        staged_experience = {item.id: item for item in self._staged.experience}

        created = tuple(
            staged_experience[experience_id].name
            for experience_id in staged_experience
            if experience_id not in baseline_experience
        )
        deleted = tuple(
            baseline_experience[experience_id].name
            for experience_id in baseline_experience
            if experience_id not in staged_experience
        )
        updated = tuple(
            staged_experience[experience_id].name
            for experience_id in staged_experience
            if experience_id in baseline_experience
            and staged_experience[experience_id].model_dump(mode="python")
            != baseline_experience[experience_id].model_dump(mode="python")
        )

        return PendingExperienceChanges(created=created, updated=updated, deleted=deleted)

    def _resolve_index(self, index: int) -> int:
        if index < 1 or index > len(self._staged.experience):
            raise IndexError(f"Experience index {index} is out of range")
        return index - 1

    def _validate_experience_file(self, data: dict[str, Any]) -> ExperienceFile:
        try:
            return ExperienceFile.model_validate(data)
        except ValidationError as exc:
            raise ValueError(str(exc)) from exc


class UserInfoEvidenceSession:
    def __init__(self, path: Path, baseline: UserInfoFile):
        self.path = path
        self._baseline = baseline
        self._staged = baseline.model_copy(deep=True)

    @classmethod
    def load(cls, path: Path | str | None = None) -> "UserInfoEvidenceSession":
        resolved_path = Path(path) if path is not None else DEFAULT_EVIDENCE_PATHS["user"]
        loaded = load_evidence_yaml(resolved_path, "user")
        if not isinstance(loaded, UserInfoFile):
            raise TypeError("Expected user evidence to load into UserInfoFile")
        return cls(resolved_path, loaded)

    @property
    def baseline(self) -> UserInfoFile:
        return self._baseline.model_copy(deep=True)

    @property
    def staged(self) -> UserInfoFile:
        return self._staged.model_copy(deep=True)

    @property
    def dirty(self) -> bool:
        return _user_info_file_to_data(self._baseline) != _user_info_file_to_data(self._staged)

    def get_user_info(self) -> UserInfoFile:
        return self._staged.model_copy(deep=True)

    def update_user_info(
        self,
        *,
        name: str,
        email: str,
        phone: str,
        linkedin: str | None,
        github: str | None,
        website: str | None,
    ) -> UserInfoFile:
        staged_data = _user_info_file_to_data(self._staged)
        staged_data.update(
            {
                "name": name,
                "email": email,
                "phone": phone,
                "linkedin": linkedin,
                "github": github,
                "website": website,
            }
        )
        validated = self._validate_user_info_file(staged_data)
        self._staged = validated
        return validated.model_copy(deep=True)

    def reload(self) -> None:
        reloaded = load_evidence_yaml(self.path, "user")
        if not isinstance(reloaded, UserInfoFile):
            raise TypeError("Expected user evidence to reload into UserInfoFile")
        self._baseline = reloaded
        self._staged = reloaded.model_copy(deep=True)

    def apply(self) -> None:
        staged_data = _user_info_file_to_data(self._staged)
        _write_yaml_atomic(self.path, staged_data, "user evidence save")
        self._baseline = self._staged.model_copy(deep=True)

    def pending_changes(self) -> PendingUserInfoChanges:
        changed_fields: list[str] = []
        for field_name in ("name", "email", "phone", "linkedin", "github", "website"):
            if getattr(self._baseline, field_name) != getattr(self._staged, field_name):
                changed_fields.append(field_name)
        return PendingUserInfoChanges(changed_fields=tuple(changed_fields))

    def _validate_user_info_file(self, data: dict[str, Any]) -> UserInfoFile:
        try:
            return UserInfoFile.model_validate(data)
        except ValidationError as exc:
            raise ValueError(str(exc)) from exc


class SkillsEvidenceSession:
    def __init__(self, path: Path, baseline: SkillsFile):
        self.path = path
        self._baseline = baseline
        self._staged = baseline.model_copy(deep=True)

    @classmethod
    def load(cls, path: Path | str | None = None) -> "SkillsEvidenceSession":
        resolved_path = Path(path) if path is not None else DEFAULT_EVIDENCE_PATHS["skills"]
        loaded = load_evidence_yaml(resolved_path, "skills")
        if not isinstance(loaded, SkillsFile):
            raise TypeError("Expected skills evidence to load into SkillsFile")
        return cls(resolved_path, loaded)

    @property
    def baseline(self) -> SkillsFile:
        return self._baseline.model_copy(deep=True)

    @property
    def staged(self) -> SkillsFile:
        return self._staged.model_copy(deep=True)

    @property
    def dirty(self) -> bool:
        return _skills_file_to_data(self._baseline) != _skills_file_to_data(self._staged)

    def get_skills(self) -> SkillsFile:
        return self._staged.model_copy(deep=True)

    def update_skills(
        self,
        *,
        technology: list[str],
        programming: list[str],
        concepts: list[str],
    ) -> SkillsFile:
        staged_data = _skills_file_to_data(self._staged)
        staged_data["skills"] = {
            "technology": technology,
            "programming": programming,
            "concepts": concepts,
        }
        validated = self._validate_skills_file(staged_data)
        self._staged = validated
        return validated.model_copy(deep=True)

    def reload(self) -> None:
        reloaded = load_evidence_yaml(self.path, "skills")
        if not isinstance(reloaded, SkillsFile):
            raise TypeError("Expected skills evidence to reload into SkillsFile")
        self._baseline = reloaded
        self._staged = reloaded.model_copy(deep=True)

    def apply(self) -> None:
        staged_data = _skills_file_to_data(self._staged)
        _write_yaml_atomic(self.path, staged_data, "skills evidence save")
        self._baseline = self._staged.model_copy(deep=True)

    def pending_changes(self) -> PendingSkillsChanges:
        changed_categories: list[str] = []
        for category in ("technology", "programming", "concepts"):
            if getattr(self._baseline.skills, category) != getattr(self._staged.skills, category):
                changed_categories.append(category)

        return PendingSkillsChanges(changed_categories=tuple(changed_categories))

    def _validate_skills_file(self, data: dict[str, Any]) -> SkillsFile:
        try:
            return SkillsFile.model_validate(data)
        except ValidationError as exc:
            raise ValueError(str(exc)) from exc
