from __future__ import annotations

from collections.abc import Iterator
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictSchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


def _normalize_slug_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _generate_record_id(name: str, existing_ids: set[str], fallback: str) -> str:
    base_slug = _normalize_slug_text(name) or fallback
    candidate = base_slug
    suffix = 2

    while candidate in existing_ids:
        candidate = f"{base_slug}-{suffix}"
        suffix += 1

    return candidate


class ProjectSkills(StrictSchemaModel):
    technology: list[str]
    programming: list[str]
    concepts: list[str]


class ProjectRecordInput(StrictSchemaModel):
    name: str
    summary: str
    highlights: list[str] = Field(min_length=1)
    active: bool
    skills: ProjectSkills
    links: list[str] | None = None


class ProjectRecord(StrictSchemaModel):
    id: str
    name: str
    summary: str
    highlights: list[str] = Field(min_length=1)
    active: bool
    skills: ProjectSkills
    links: list[str] | None = None


class ProjectsFile(StrictSchemaModel):
    schema_version: Literal[1]
    projects: list[ProjectRecord]

    @model_validator(mode="after")
    def validate_unique_project_ids(self) -> "ProjectsFile":
        seen_ids: set[str] = set()
        duplicate_ids: set[str] = set()

        for project in self.projects:
            if project.id in seen_ids:
                duplicate_ids.add(project.id)
            seen_ids.add(project.id)

        if duplicate_ids:
            duplicates = ", ".join(sorted(duplicate_ids))
            raise ValueError(f"Duplicate project ids are not allowed: {duplicates}")

        return self

    def iter_projects(self) -> Iterator[ProjectRecord]:
        return iter(self.projects)

    def projects_by_id(self) -> dict[str, ProjectRecord]:
        return {project.id: project for project in self.projects}


class ExperienceRecord(StrictSchemaModel):
    id: str
    name: str
    role: str
    summary: str
    highlights: list[str] = Field(min_length=1)
    active: bool
    skills: ProjectSkills
    location: str
    start: str
    end: str | None = None
    links: list[str] | None = None


class ExperienceRecordInput(StrictSchemaModel):
    name: str
    role: str
    summary: str
    highlights: list[str] = Field(min_length=1)
    active: bool
    skills: ProjectSkills
    location: str
    start: str
    end: str | None = None
    links: list[str] | None = None


class ExperienceFile(StrictSchemaModel):
    schema_version: Literal[1]
    experience: list[ExperienceRecord]

    @model_validator(mode="after")
    def validate_unique_experience_ids(self) -> "ExperienceFile":
        seen_ids: set[str] = set()
        duplicate_ids: set[str] = set()

        for experience in self.experience:
            if experience.id in seen_ids:
                duplicate_ids.add(experience.id)
            seen_ids.add(experience.id)

        if duplicate_ids:
            duplicates = ", ".join(sorted(duplicate_ids))
            raise ValueError(f"Duplicate experience ids are not allowed: {duplicates}")

        return self

    def iter_experience(self) -> Iterator[ExperienceRecord]:
        return iter(self.experience)

    def experience_by_id(self) -> dict[str, ExperienceRecord]:
        return {experience.id: experience for experience in self.experience}


class SkillsFile(StrictSchemaModel):
    schema_version: Literal[1]
    skills: ProjectSkills


class SkillsInput(StrictSchemaModel):
    skills: ProjectSkills


class EducationRecord(StrictSchemaModel):
    id: str
    name: str
    degree: str
    grade: str
    start: str
    end: str | None = None
    location: str
    relevant_coursework: list[str]


class EducationRecordInput(StrictSchemaModel):
    name: str
    degree: str
    grade: str
    start: str
    end: str | None = None
    location: str
    relevant_coursework: list[str]


class EducationFile(StrictSchemaModel):
    schema_version: Literal[1]
    education: list[EducationRecord]

    @model_validator(mode="before")
    @classmethod
    def fill_missing_education_ids(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        raw_education = data.get("education")
        if not isinstance(raw_education, list):
            return data

        normalized_data = dict(data)
        normalized_education: list[Any] = []
        existing_ids = {
            item.get("id")
            for item in raw_education
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }

        for item in raw_education:
            if not isinstance(item, dict) or item.get("id"):
                normalized_education.append(item)
                continue

            normalized_item = dict(item)
            name = normalized_item.get("name")
            normalized_item["id"] = _generate_record_id(
                name if isinstance(name, str) else "",
                existing_ids,
                "education",
            )
            existing_ids.add(normalized_item["id"])
            normalized_education.append(normalized_item)

        normalized_data["education"] = normalized_education
        return normalized_data

    @model_validator(mode="after")
    def validate_unique_education_ids(self) -> "EducationFile":
        seen_ids: set[str] = set()
        duplicate_ids: set[str] = set()

        for education in self.education:
            if education.id in seen_ids:
                duplicate_ids.add(education.id)
            seen_ids.add(education.id)

        if duplicate_ids:
            duplicates = ", ".join(sorted(duplicate_ids))
            raise ValueError(f"Duplicate education ids are not allowed: {duplicates}")

        return self


class UserInfoFile(StrictSchemaModel):
    schema_version: Literal[1]
    name: str
    email: str
    phone: str
    linkedin: str | None = None
    github: str | None = None
    website: str | None = None

    @field_validator("name", "email", "phone")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("required contact fields must not be empty")
        return normalized

    @field_validator("linkedin", "github", "website")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("optional contact links must not be empty when provided")
        return normalized


class UserInfoInput(StrictSchemaModel):
    name: str
    email: str
    phone: str
    linkedin: str | None = None
    github: str | None = None
    website: str | None = None

    @field_validator("name", "email", "phone")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("required contact fields must not be empty")
        return normalized

    @field_validator("linkedin", "github", "website")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("optional contact links must not be empty when provided")
        return normalized


class ResumeEvidenceRegistry(StrictSchemaModel):
    education: EducationFile
    experience: ExperienceFile
    projects: ProjectsFile
    skills: SkillsFile
    user: UserInfoFile
