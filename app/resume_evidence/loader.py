from __future__ import annotations

from pathlib import Path
from typing import Mapping

import yaml
from pydantic import BaseModel

from app.resume_evidence.models import ProjectsFile

_REPO_ROOT = Path(__file__).resolve().parents[2]

SCHEMA_REGISTRY: dict[str, type[BaseModel]] = {
    "projects": ProjectsFile,
}

DEFAULT_EVIDENCE_PATHS: dict[str, Path] = {
    "projects": _REPO_ROOT / "user" / "resume_evidence" / "projects.yaml",
}


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
    evidence_paths = dict(DEFAULT_EVIDENCE_PATHS)
    if paths is not None:
        evidence_paths.update({schema_name: Path(path) for schema_name, path in paths.items()})

    loaded_evidence: dict[str, BaseModel] = {}
    for schema_name in sorted(SCHEMA_REGISTRY):
        path = evidence_paths.get(schema_name)
        if path is None:
            raise ValueError(f"No evidence path configured for schema '{schema_name}'")
        loaded_evidence[schema_name] = load_evidence_yaml(path, schema_name)

    return loaded_evidence
