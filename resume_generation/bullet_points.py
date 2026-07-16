from __future__ import annotations

from typing import Any, Iterable

import httpx

from app.config import settings
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


def _effective_bullet_count_range(payload: dict[str, Any]) -> tuple[int, int]:
    count_range = payload.get("bullet_count_range")
    if isinstance(count_range, dict):
        min_count = count_range.get("min")
        max_count = count_range.get("max")
        if isinstance(min_count, int) and isinstance(max_count, int):
            return min_count, max_count

    default_count = settings.BULLETPOINTS_DEFAULT_COUNT
    return default_count, default_count


def _bullet_count_matches_request(
    response_data: dict[str, Any],
    *,
    payload: dict[str, Any],
) -> bool:
    bullet_points = response_data.get("bullet_points")
    if not isinstance(bullet_points, list):
        return False

    min_count, max_count = _effective_bullet_count_range(payload)
    return min_count <= len(bullet_points) <= max_count


def _bullet_dev_mode(payload: dict[str, Any]) -> bool:
    return bool(payload.get("dev_mode", settings.DEV_MODE))


def _bullet_cache_payload(
    payload: dict[str, Any],
    *,
    evidence_type: str,
) -> dict[str, Any]:
    evidence_payload = payload.get(evidence_type)
    return {
        "context": payload.get("context"),
        "evidence_type": evidence_type,
        evidence_type: evidence_payload,
        "llm_model": payload.get("llm_model", settings.BULLETPOINTS_LLM_MODEL),
    }


def _bullet_fetch_payload(payload: dict[str, Any]) -> dict[str, Any]:
    fetch_payload = dict(payload)
    fetch_payload["dev_mode"] = True
    return fetch_payload


def _shape_bullet_response(
    response_data: dict[str, Any],
    *,
    payload: dict[str, Any],
) -> dict[str, Any]:
    shaped = {"bullet_points": response_data.get("bullet_points", [])}
    if _bullet_dev_mode(payload):
        details = response_data.get("details")
        if details is not None:
            shaped["details"] = details
    return shaped


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
                cache_payload=_bullet_cache_payload(
                    payload,
                    evidence_type="project",
                ),
                fetch_payload=_bullet_fetch_payload(payload),
                namespace=project.id,
                should_use_cached=lambda data, request_payload=payload: (
                    _bullet_count_matches_request(data, payload=request_payload)
                ),
                token_usage_monitor=token_usage_monitor,
                stage_response_records=stage_response_records,
            )
            if cache is not None:
                response = _shape_bullet_response(response, payload=payload)
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
                cache_payload=_bullet_cache_payload(
                    payload,
                    evidence_type="experience",
                ),
                fetch_payload=_bullet_fetch_payload(payload),
                namespace=item.id,
                should_use_cached=lambda data, request_payload=payload: (
                    _bullet_count_matches_request(data, payload=request_payload)
                ),
                token_usage_monitor=token_usage_monitor,
                stage_response_records=stage_response_records,
            )
            if cache is not None:
                response = _shape_bullet_response(response, payload=payload)
            results.append(
                ExperienceBulletPointResult(
                    experience_id=item.id,
                    bullet_points=response["bullet_points"],
                    details=response.get("details"),
                )
            )

    return results
