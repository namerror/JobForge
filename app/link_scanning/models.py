from __future__ import annotations

from typing import Any

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
    llm_model: str | None = None
    llm_max_output_tokens: int | None = None

    @field_validator("llm_model")
    @classmethod
    def validate_llm_model(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("llm_model must not be empty")
        return normalized

    @field_validator("llm_max_output_tokens")
    @classmethod
    def validate_llm_max_output_tokens(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("llm_max_output_tokens must be greater than 0")
        return value


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


class LinkScanResponse(StrictSchemaModel):
    project_id: str
    added_highlights: list[LinkScanHighlight]
    details: dict[str, Any] | None = None
