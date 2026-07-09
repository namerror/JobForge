from __future__ import annotations

from typing import Iterable

import httpx

from resume_evidence.models import ExperienceRecord, ProjectRecord
from resume_generation.cache import ResumeGenerationStageCache
from resume_generation.models import (
    ExperienceBulletPointResult,
    JobTarget,
    ProjectBulletPointResult,
    ResumeGenerationConfig,
)
from resume_generation.selection import _cached_post_json, _exclude_none
from resume_generation.token_usage import ResumeGenerationTokenUsageMonitor


def generate_project_bullet_points(
    *,
    selected_projects: Iterable[ProjectRecord],
    config: ResumeGenerationConfig,
    job_target: JobTarget,
    cache: ResumeGenerationStageCache | None = None,
    token_usage_monitor: ResumeGenerationTokenUsageMonitor | None = None,
    stage_response_records: list[dict] | None = None,
) -> list[ProjectBulletPointResult]:
    bullet_config = _exclude_none(config.project_bullet_point_generation)

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
            response = _cached_post_json(
                cache=cache,
                stage="project_bullet_points",
                client=client,
                endpoint="/generate-bulletpoints",
                payload=payload,
                namespace=project.id,
                token_usage_monitor=token_usage_monitor,
                stage_response_records=stage_response_records,
            )
            results.append(
                ProjectBulletPointResult(
                    project_id=project.id,
                    bullet_points=response["bullet_points"],
                    details=response.get("details"),
                )
            )

    return results


def generate_experience_bullet_points(
    *,
    experience: Iterable[ExperienceRecord],
    config: ResumeGenerationConfig,
    job_target: JobTarget,
    cache: ResumeGenerationStageCache | None = None,
    token_usage_monitor: ResumeGenerationTokenUsageMonitor | None = None,
    stage_response_records: list[dict] | None = None,
) -> list[ExperienceBulletPointResult]:
    bullet_config = _exclude_none(config.experience_bullet_point_generation)

    results: list[ExperienceBulletPointResult] = []
    with httpx.Client(
        base_url=config.app.base_url,
        timeout=config.app.timeout_seconds,
    ) as client:
        for item in experience:
            if not item.active:
                continue
            payload = {
                "context": {
                    "title": job_target.title,
                    "description": job_target.description,
                },
                "experience": item.model_dump(),
                **bullet_config,
            }
            response = _cached_post_json(
                cache=cache,
                stage="experience_bullet_points",
                client=client,
                endpoint="/generate-bulletpoints",
                payload=payload,
                namespace=item.id,
                token_usage_monitor=token_usage_monitor,
                stage_response_records=stage_response_records,
            )
            results.append(
                ExperienceBulletPointResult(
                    experience_id=item.id,
                    bullet_points=response["bullet_points"],
                    details=response.get("details"),
                )
            )

    return results
