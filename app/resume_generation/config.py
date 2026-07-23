from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.resume_generation.models import JobTarget, ResumeGenerationConfig

_REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_GENERATION_CONFIG_PATH = _REPO_ROOT / "user" / "resume_generation" / "config.yaml"
DEFAULT_JOB_TARGET_PATH = _REPO_ROOT / "user" / "resume_generation" / "job_target.yaml"


def _load_yaml_mapping(path: Path | str) -> dict[str, Any]:
    yaml_path = Path(path)
    with yaml_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping in {yaml_path}")
    return data


def load_generation_config(path: Path | str = DEFAULT_GENERATION_CONFIG_PATH) -> ResumeGenerationConfig:
    return ResumeGenerationConfig.model_validate(_load_yaml_mapping(path))


def load_job_target(path: Path | str = DEFAULT_JOB_TARGET_PATH) -> JobTarget:
    return JobTarget.model_validate(_load_yaml_mapping(path))
