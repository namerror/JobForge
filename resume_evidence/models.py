from __future__ import annotations

from collections.abc import Iterator
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictSchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ProjectSkills(StrictSchemaModel):
    technology: list[str]
    programming: list[str]
    concepts: list[str]


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


class SkillsFile(StrictSchemaModel):
    schema_version: Literal[1]
    skills: ProjectSkills


class UserInfoFile(StrictSchemaModel):
    schema_version: Literal[1]
    name: str
    email: str
    phone: str
    linkedin: str | None = None
    github: str | None = None

    @field_validator("name", "email", "phone")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("required contact fields must not be empty")
        return normalized

    @field_validator("linkedin", "github")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("optional contact links must not be empty when provided")
        return normalized
