from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from resume_evidence.models import ProjectRecord


class StrictSchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class BulletJobContext(StrictSchemaModel):
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


class BulletCountRange(StrictSchemaModel):
    min: int
    max: int

    @model_validator(mode="after")
    def validate_range(self) -> "BulletCountRange":
        if self.min < 1:
            raise ValueError("bullet_count_range.min must be greater than or equal to 1")
        if self.max > 10:
            raise ValueError("bullet_count_range.max must be less than or equal to 10")
        if self.min > self.max:
            raise ValueError("bullet_count_range.min must be less than or equal to max")
        return self


class BulletGenerationRequest(StrictSchemaModel):
    context: BulletJobContext
    project: ProjectRecord
    bullet_count_range: BulletCountRange | None = None
    dev_mode: bool | None = None
    llm_model: str | None = None
    llm_max_output_tokens: int | None = None
    link_scanning: bool | None = None

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


class BulletGenerationResponse(StrictSchemaModel):
    bullet_points: list[str]
    details: dict[str, Any] | None = None
