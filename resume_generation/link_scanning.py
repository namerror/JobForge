from __future__ import annotations

from typing import Iterable

import httpx

from resume_evidence.models import ProjectRecord
from resume_generation.cache import ResumeGenerationStageCache
from resume_generation.models import (
    JobTarget,
    ProjectLinkScanResult,
    ResumeGenerationConfig,
)
from resume_generation.selection import _cached_post_json
from resume_generation.token_usage import ResumeGenerationTokenUsageMonitor


def enrich_projects_with_link_scanning(
    *,
    selected_projects: Iterable[ProjectRecord],
    config: ResumeGenerationConfig,
    job_target: JobTarget,
    cache: ResumeGenerationStageCache | None = None,
    token_usage_monitor: ResumeGenerationTokenUsageMonitor | None = None,
    stage_response_records: list[dict] | None = None,
) -> list[ProjectRecord]:
    projects = list(selected_projects)
    if not config.link_scanning.enabled:
        return projects

    enriched_projects: list[ProjectRecord] = []
    with httpx.Client(
        base_url=config.app.base_url,
        timeout=config.app.timeout_seconds,
    ) as client:
        for project in projects:
            if not project.links:
                enriched_projects.append(project)
                continue

            payload = {
                "context": {
                    "title": job_target.title,
                    "description": job_target.description,
                },
                "project": project.model_dump(),
                "dev_mode": config.link_scanning.dev_mode,
                "llm_model": config.link_scanning.llm_model,
                "llm_max_output_tokens": config.link_scanning.llm_max_output_tokens,
            }
            response = _cached_post_json(
                cache=cache,
                stage="link_scanning",
                client=client,
                endpoint="/scan-link",
                payload={key: value for key, value in payload.items() if value is not None},
                namespace=project.id,
                token_usage_monitor=token_usage_monitor,
                stage_response_records=stage_response_records,
            )
            scan_result = ProjectLinkScanResult.model_validate(response)
            enriched_projects.append(_apply_link_scan_result(project, scan_result))

    return enriched_projects


def _apply_link_scan_result(
    project: ProjectRecord,
    scan_result: ProjectLinkScanResult,
) -> ProjectRecord:
    highlights = [*project.highlights, *[item.text for item in scan_result.added_highlights]]

    return project.model_copy(
        update={
            "highlights": highlights,
        }
    )
