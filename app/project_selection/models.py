from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from app.resume_evidence.models import ProjectSkills


class StrictSchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ProjectJobContext(StrictSchemaModel):
    title: str
    description: str | None = None


class ProjectCandidate(StrictSchemaModel):
    id: str
    name: str
    summary: str
    skills: ProjectSkills


class RankedProject(StrictSchemaModel):
    project_id: str
    score: float
    method: Literal["baseline", "llm"]


class ProjectSelectionResult(StrictSchemaModel):
    selected_project_ids: list[str]
    ranked_projects: list[RankedProject]
    details: dict[str, Any] | None = None


class ProjectSelectRequest(StrictSchemaModel):
    context: ProjectJobContext
    candidates: list[ProjectCandidate]
    method: Literal["baseline", "llm"] | None = None
    top_n: int | None = None
    dev_mode: bool | None = None
