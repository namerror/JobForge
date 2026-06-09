from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from resume_evidence.models import ProjectRecord


class StrictSchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class GenerationAppConfig(StrictSchemaModel):
    base_url: str = "http://127.0.0.1:8000"
    timeout_seconds: float = 30.0

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        normalized = value.strip().rstrip("/")
        if not normalized:
            raise ValueError("base_url must not be empty")
        return normalized

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("timeout_seconds must be greater than 0")
        return value


class SkillSelectionConfig(StrictSchemaModel):
    method: Literal["baseline", "embeddings", "llm"] | None = None
    top_n: int | None = None
    baseline_filter: bool | None = None
    dev_mode: bool | None = None
    llm_model: str | None = None
    llm_max_output_tokens: int | None = None

    @field_validator("top_n")
    @classmethod
    def validate_top_n(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("top_n must be greater than or equal to 0")
        return value

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


class ProjectSelectionConfig(StrictSchemaModel):
    method: Literal["baseline", "llm"] | None = None
    top_n: int | None = None
    dev_mode: bool | None = None
    llm_model: str | None = None
    llm_max_output_tokens: int | None = None

    @field_validator("top_n")
    @classmethod
    def validate_top_n(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("top_n must be greater than or equal to 0")
        return value

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


class BulletCountRangeConfig(StrictSchemaModel):
    min: int
    max: int

    @field_validator("min")
    @classmethod
    def validate_min(cls, value: int) -> int:
        if value < 1:
            raise ValueError("bullet_count_range.min must be greater than or equal to 1")
        return value

    @field_validator("max")
    @classmethod
    def validate_max(cls, value: int) -> int:
        if value > 10:
            raise ValueError("bullet_count_range.max must be less than or equal to 10")
        return value

    @model_validator(mode="after")
    def validate_range(self) -> "BulletCountRangeConfig":
        if self.min > self.max:
            raise ValueError("bullet_count_range.min must be less than or equal to max")
        return self


class BulletPointGenerationConfig(StrictSchemaModel):
    bullet_count_range: BulletCountRangeConfig | None = None
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


class LinkScanningConfig(StrictSchemaModel):
    enabled: bool = False
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


class ResumeGenerationConfig(StrictSchemaModel):
    schema_version: Literal[1]
    app: GenerationAppConfig = Field(default_factory=GenerationAppConfig)
    skill_selection: SkillSelectionConfig = Field(default_factory=SkillSelectionConfig)
    project_selection: ProjectSelectionConfig = Field(default_factory=ProjectSelectionConfig)
    link_scanning: LinkScanningConfig = Field(default_factory=LinkScanningConfig)
    bullet_point_generation: BulletPointGenerationConfig = Field(
        default_factory=BulletPointGenerationConfig
    )


class JobTarget(StrictSchemaModel):
    schema_version: Literal[1]
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


class SkillSelectionResult(StrictSchemaModel):
    technology: list[str]
    programming: list[str]
    concepts: list[str]
    details: dict[str, Any] | None = None


class RankedProjectResult(StrictSchemaModel):
    project_id: str
    score: float
    method: Literal["baseline", "llm"]


class ProjectSelectionResult(StrictSchemaModel):
    selected_project_ids: list[str]
    ranked_projects: list[RankedProjectResult]
    details: dict[str, Any] | None = None


class ResumeSelectionContext(StrictSchemaModel):
    job_target: JobTarget
    selected_skills: SkillSelectionResult
    project_selection: ProjectSelectionResult
    selected_projects: list[ProjectRecord]
    config_path: Path
    job_target_path: Path
    evidence_paths: dict[str, Path]


class ProjectBulletPointResult(StrictSchemaModel):
    project_id: str
    bullet_points: list[str]
    details: dict[str, Any] | None = None


class LinkScanHighlight(StrictSchemaModel):
    text: str
    source_url: str


class ProjectLinkScanResult(StrictSchemaModel):
    project_id: str
    added_highlights: list[LinkScanHighlight]
    details: dict[str, Any] | None = None
