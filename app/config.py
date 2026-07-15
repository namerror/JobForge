from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


SkillSelectionMethod = Literal["baseline", "embeddings", "llm"]
ProjectSelectionMethod = Literal["baseline", "llm"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    SKILL_TOP_N: int = 10
    SKILL_METHOD: SkillSelectionMethod = "baseline"
    SKILL_BASELINE_FILTER: bool = False
    PROJ_TOP_N: int | None = None
    PROJ_METHOD: ProjectSelectionMethod = "llm"
    DEV_MODE: bool = True
    LOG_LEVEL: str = "INFO"

    # Embedding-related settings, only relevant if SKILL_METHOD=embeddings
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_BATCH_SIZE: int = 100
    # EMBEDDING_DIMENSIONS: int = 1024 # Optionally reduce dimensionality

    # LLM-related settings, split by subsystem so selection methods can be tuned independently.
    SKILL_LLM_MODEL: str = "gpt-5-mini"
    SKILL_LLM_MAX_OUTPUT_TOKENS: int = 1200
    PROJ_LLM_MODEL: str = "gpt-5-mini"
    PROJ_LLM_MAX_OUTPUT_TOKENS: int = 1200
    BULLETPOINTS_LLM_MODEL: str = "gpt-5-mini"
    BULLETPOINTS_LLM_MAX_OUTPUT_TOKENS: int = 3000
    BULLETPOINTS_DEFAULT_COUNT: int = 3
    LINK_SCANNING_ENABLED: bool = False
    LINK_SCANNING_LLM_MODEL: str = "gpt-5-mini"
    LINK_SCANNING_LLM_MAX_OUTPUT_TOKENS: int = 1200

    OPENAI_API_KEY: str = "" # This should be set in the .env file or environment variable

    @field_validator("SKILL_METHOD", "PROJ_METHOD", mode="before")
    @classmethod
    def normalize_method(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("BULLETPOINTS_DEFAULT_COUNT")
    @classmethod
    def validate_bulletpoints_default_count(cls, value: int) -> int:
        if value < 1 or value > 10:
            raise ValueError("BULLETPOINTS_DEFAULT_COUNT must be between 1 and 10")
        return value

    @field_validator(
        "SKILL_LLM_MAX_OUTPUT_TOKENS",
        "BULLETPOINTS_LLM_MAX_OUTPUT_TOKENS",
        "LINK_SCANNING_LLM_MAX_OUTPUT_TOKENS",
    )
    @classmethod
    def validate_llm_max_output_tokens(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("LLM max output tokens must be greater than 0")
        return value


settings = Settings()
