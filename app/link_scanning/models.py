from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from resume_evidence.models import ExperienceRecord, ProjectRecord


class StrictSchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class LinkScanRequest(StrictSchemaModel):
    evidence_type: Literal["project", "experience"]
    evidence: ProjectRecord | ExperienceRecord
    dev_mode: bool | None = None
    llm_model: str | None = None
    llm_max_output_tokens: int | None = None
    requested_highlight_count: int | None = None
    max_tokens_per_highlight: int | None = None

    @model_validator(mode="before")
    @classmethod
    def accept_legacy_project_payload(cls, data: Any) -> Any:
        if isinstance(data, dict) and "project" in data and "evidence" not in data:
            normalized = dict(data)
            normalized["evidence_type"] = "project"
            normalized["evidence"] = normalized.pop("project")
            normalized.pop("context", None)
            return normalized
        return data

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

    @field_validator("requested_highlight_count")
    @classmethod
    def validate_requested_highlight_count(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("requested_highlight_count must be greater than 0")
        return value

    @field_validator("max_tokens_per_highlight")
    @classmethod
    def validate_max_tokens_per_highlight(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("max_tokens_per_highlight must be greater than 0")
        return value

    @model_validator(mode="after")
    def validate_evidence_type_matches_record(self) -> "LinkScanRequest":
        if self.evidence_type == "project" and not isinstance(self.evidence, ProjectRecord):
            raise ValueError("project link scans require a ProjectRecord")
        if self.evidence_type == "experience" and not isinstance(
            self.evidence, ExperienceRecord
        ):
            raise ValueError("experience link scans require an ExperienceRecord")
        return self


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
    evidence_type: Literal["project", "experience"]
    evidence_id: str
    added_highlights: list[LinkScanHighlight]
    details: dict[str, Any] | None = None
