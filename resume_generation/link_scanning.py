from __future__ import annotations

from typing import Iterable

import httpx

from resume_evidence.models import ProjectRecord, ProjectSkills
from resume_generation.models import (
    JobTarget,
    ProjectLinkScanResult,
    ResumeGenerationConfig,
)
from resume_generation.selection import _post_json


def enrich_projects_with_link_scanning(
    *,
    selected_projects: Iterable[ProjectRecord],
    config: ResumeGenerationConfig,
    job_target: JobTarget,
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
            }
            response = _post_json(
                client,
                "/scan-link",
                {key: value for key, value in payload.items() if value is not None},
            )
            scan_result = ProjectLinkScanResult.model_validate(response)
            enriched_projects.append(_apply_link_scan_result(project, scan_result))

    return enriched_projects


def _apply_link_scan_result(
    project: ProjectRecord,
    scan_result: ProjectLinkScanResult,
) -> ProjectRecord:
    highlights = [*project.highlights, *[item.text for item in scan_result.added_highlights]]
    skills_payload = project.skills.model_dump()

    for skill in scan_result.added_skills:
        category_skills = skills_payload[skill.category]
        if skill.name not in category_skills:
            category_skills.append(skill.name)

    return project.model_copy(
        update={
            "highlights": highlights,
            "skills": ProjectSkills.model_validate(skills_payload),
        }
    )
