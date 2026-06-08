from __future__ import annotations

from typing import Iterable

import httpx

from resume_evidence.models import ProjectRecord
from resume_generation.models import (
    JobTarget,
    ProjectBulletPointResult,
    ResumeGenerationConfig,
)
from resume_generation.selection import _exclude_none, _post_json


def generate_project_bullet_points(
    *,
    selected_projects: Iterable[ProjectRecord],
    config: ResumeGenerationConfig,
    job_target: JobTarget,
) -> list[ProjectBulletPointResult]:
    bullet_config = _exclude_none(config.bullet_point_generation)

    results: list[ProjectBulletPointResult] = []
    with httpx.Client(
        base_url=config.app.base_url,
        timeout=config.app.timeout_seconds,
    ) as client:
        for project in selected_projects:
            payload = {
                "context": {
                    "title": job_target.title,
                    "description": job_target.description,
                },
                "project": project.model_dump(),
                **bullet_config,
            }
            response = _post_json(client, "/generate-bulletpoints", payload)
            results.append(
                ProjectBulletPointResult(
                    project_id=project.id,
                    bullet_points=response["bullet_points"],
                    details=response.get("details"),
                )
            )

    return results
