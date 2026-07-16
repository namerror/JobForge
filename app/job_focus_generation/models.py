from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class StrictSchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class JobFocus(StrictSchemaModel):
    summary: str
    required_skills: list[str]
    preferred_skills: list[str]
    responsibilities: list[str]
    domain_emphasis: list[str]
    resume_relevant_constraints: list[str]
    excluded_context: list[str]

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("summary must not be empty")
        return normalized

    @field_validator(
        "required_skills",
        "preferred_skills",
        "responsibilities",
        "domain_emphasis",
        "resume_relevant_constraints",
        "excluded_context",
    )
    @classmethod
    def validate_string_list(cls, value: list[str]) -> list[str]:
        normalized = [item.strip() for item in value if item.strip()]
        return list(dict.fromkeys(normalized))


class JobFocusRequest(StrictSchemaModel):
    title: str
    description: str | None = None
    dev_mode: bool | None = None
    llm_model: str | None = None
    llm_max_output_tokens: int | None = None

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


class JobFocusResponse(StrictSchemaModel):
    job_focus: JobFocus
    details: dict[str, Any] | None = None
