from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    TOP_N: int = 10
    METHOD: str = "baseline"
    DEV_MODE: bool = True
    LOG_LEVEL: str = "INFO"

settings = Settings()