import pytest
from pydantic import ValidationError

from app.config import Settings


SCOPED_ENV_VARS = [
    "SKILL_METHOD",
    "SKILL_TOP_N",
    "SKILL_BASELINE_FILTER",
    "PROJ_METHOD",
    "PROJ_TOP_N",
    "SKILL_LLM_MODEL",
    "SKILL_LLM_MAX_OUTPUT_TOKENS",
    "PROJ_LLM_MODEL",
    "PROJ_LLM_MAX_OUTPUT_TOKENS",
    "BULLETPOINTS_LLM_MODEL",
    "BULLETPOINTS_LLM_MAX_OUTPUT_TOKENS",
    "BULLETPOINTS_DEFAULT_COUNT",
    "LINK_SCANNING_ENABLED",
]
LEGACY_ENV_VARS = [
    "METHOD",
    "TOP_N",
    "BASELINE_FILTER",
    "LLM_MODEL",
    "LLM_MAX_OUTPUT_TOKENS",
]


def _clear_selection_env(monkeypatch):
    for name in SCOPED_ENV_VARS + LEGACY_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def test_settings_scoped_defaults(monkeypatch):
    _clear_selection_env(monkeypatch)

    settings = Settings(_env_file=None)

    assert settings.SKILL_METHOD == "baseline"
    assert settings.SKILL_TOP_N == 10
    assert settings.SKILL_BASELINE_FILTER is False
    assert settings.PROJ_METHOD == "llm"
    assert settings.PROJ_TOP_N is None
    assert settings.SKILL_LLM_MODEL == "gpt-5-mini"
    assert settings.PROJ_LLM_MODEL == "gpt-5-mini"
    assert settings.SKILL_LLM_MAX_OUTPUT_TOKENS == 1200
    assert settings.PROJ_LLM_MAX_OUTPUT_TOKENS == 1200
    assert settings.BULLETPOINTS_LLM_MODEL == "gpt-5-mini"
    assert settings.BULLETPOINTS_LLM_MAX_OUTPUT_TOKENS == 1200
    assert settings.BULLETPOINTS_DEFAULT_COUNT == 3
    assert settings.LINK_SCANNING_ENABLED is False


def test_settings_bulletpoints_env_overrides(monkeypatch):
    _clear_selection_env(monkeypatch)
    monkeypatch.setenv("BULLETPOINTS_LLM_MODEL", "writer-model")
    monkeypatch.setenv("BULLETPOINTS_LLM_MAX_OUTPUT_TOKENS", "777")
    monkeypatch.setenv("BULLETPOINTS_DEFAULT_COUNT", "4")
    monkeypatch.setenv("LINK_SCANNING_ENABLED", "true")

    settings = Settings(_env_file=None)

    assert settings.BULLETPOINTS_LLM_MODEL == "writer-model"
    assert settings.BULLETPOINTS_LLM_MAX_OUTPUT_TOKENS == 777
    assert settings.BULLETPOINTS_DEFAULT_COUNT == 4
    assert settings.LINK_SCANNING_ENABLED is True


def test_settings_validates_bulletpoints_defaults(monkeypatch):
    _clear_selection_env(monkeypatch)
    monkeypatch.setenv("BULLETPOINTS_DEFAULT_COUNT", "0")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)

    _clear_selection_env(monkeypatch)
    monkeypatch.setenv("BULLETPOINTS_LLM_MAX_OUTPUT_TOKENS", "0")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_normalizes_methods(monkeypatch):
    _clear_selection_env(monkeypatch)
    monkeypatch.setenv("SKILL_METHOD", " LLM ")
    monkeypatch.setenv("PROJ_METHOD", "BASELINE")

    settings = Settings(_env_file=None)

    assert settings.SKILL_METHOD == "llm"
    assert settings.PROJ_METHOD == "baseline"


def test_settings_validates_methods(monkeypatch):
    _clear_selection_env(monkeypatch)
    monkeypatch.setenv("SKILL_METHOD", "projector")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)

    _clear_selection_env(monkeypatch)
    monkeypatch.setenv("PROJ_METHOD", "embeddings")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_legacy_selection_env_vars_are_not_honored(monkeypatch):
    _clear_selection_env(monkeypatch)
    monkeypatch.setenv("METHOD", "llm")
    monkeypatch.setenv("TOP_N", "2")
    monkeypatch.setenv("BASELINE_FILTER", "true")
    monkeypatch.setenv("LLM_MODEL", "legacy-model")
    monkeypatch.setenv("LLM_MAX_OUTPUT_TOKENS", "77")

    settings = Settings(_env_file=None)

    assert settings.SKILL_METHOD == "baseline"
    assert settings.SKILL_TOP_N == 10
    assert settings.SKILL_BASELINE_FILTER is False
    assert settings.SKILL_LLM_MODEL == "gpt-5-mini"
    assert settings.PROJ_LLM_MODEL == "gpt-5-mini"
    assert settings.SKILL_LLM_MAX_OUTPUT_TOKENS == 1200
    assert settings.PROJ_LLM_MAX_OUTPUT_TOKENS == 1200
    assert settings.BULLETPOINTS_LLM_MODEL == "gpt-5-mini"
