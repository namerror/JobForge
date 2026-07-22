from __future__ import annotations

from pathlib import Path
from typing import Mapping

import yaml
from pydantic import BaseModel

from app.config import settings
from app.resume_evidence.models import (
    EducationFile,
    ExperienceFile,
    ProjectsFile,
    SkillsFile,
    UserInfoFile,
)

SCHEMA_REGISTRY: dict[str, type[BaseModel]] = {
    "education": EducationFile,
    "experience": ExperienceFile,
    "projects": ProjectsFile,
    "skills": SkillsFile,
    "user": UserInfoFile,
}

def default_evidence_paths(root: Path | str | None = None) -> dict[str, Path]:
    evidence_root = Path(root if root is not None else settings.RESUME_EVIDENCE_ROOT)
    return {
        "education": evidence_root / "education.yaml",
        "experience": evidence_root / "experience.yaml",
        "projects": evidence_root / "projects.yaml",
        "skills": evidence_root / "skills.yaml",
        "user": evidence_root / "user.yaml",
    }


DEFAULT_EVIDENCE_PATHS: dict[str, Path] = default_evidence_paths()


def load_evidence_yaml(path: Path | str, schema_name: str) -> BaseModel:
    schema_model = SCHEMA_REGISTRY.get(schema_name)
    if schema_model is None:
        supported_schemas = ", ".join(sorted(SCHEMA_REGISTRY))
        raise ValueError(
            f"Unsupported evidence schema '{schema_name}'. Supported schemas: {supported_schemas}"
        )

    yaml_path = Path(path)
    with yaml_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    return schema_model.model_validate(data)


def load_registered_evidence(
    paths: Mapping[str, Path | str] | None = None,
) -> dict[str, BaseModel]:
    evidence_paths = default_evidence_paths()
    if paths is not None:
        evidence_paths.update({schema_name: Path(path) for schema_name, path in paths.items()})

    loaded_evidence: dict[str, BaseModel] = {}
    for schema_name in sorted(SCHEMA_REGISTRY):
        path = evidence_paths.get(schema_name)
        if path is None:
            raise ValueError(f"No evidence path configured for schema '{schema_name}'")
        loaded_evidence[schema_name] = load_evidence_yaml(path, schema_name)

    return loaded_evidence
