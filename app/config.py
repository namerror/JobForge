from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    TOP_N: int = 10
    METHOD: str = "baseline"
    DEV_MODE: bool = True
    LOG_LEVEL: str = "INFO"

    # Embedding-related settings, only relevant if METHOD=embeddings
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_BATCH_SIZE: int = 100
    # EMBEDDING_DIMENSIONS: int = 1024 # Optionally reduce dimensionality

    # LLM-related settings, only relevant if METHOD=llm
    LLM_MODEL: str = "gpt-5-mini"
    LLM_MAX_OUTPUT_TOKENS: int = 1200
    
    OPENAI_API_KEY: str = "" # This should be set in the .env file or environment variable

settings = Settings()
