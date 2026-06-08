from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator

from resume_evidence.models import ProjectRecord


class StrictSchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class LinkScanJobContext(StrictSchemaModel):
    title: str
    description: str | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("title must not be empty")
        return normalized

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()


class LinkScanRequest(StrictSchemaModel):
    context: LinkScanJobContext
    project: ProjectRecord
    dev_mode: bool | None = None


class LinkScanHighlight(StrictSchemaModel):
    text: str
    source_url: str

    @field_validator("text", "source_url")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("value must not be empty")
        return normalized


class LinkScanSkill(StrictSchemaModel):
    name: str
    category: Literal["technology", "programming", "concepts"]
    source_url: str

    @field_validator("name", "source_url")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("value must not be empty")
        return normalized


class LinkScanResponse(StrictSchemaModel):
    project_id: str
    added_highlights: list[LinkScanHighlight]
    added_skills: list[LinkScanSkill]
    details: dict[str, Any] | None = None

