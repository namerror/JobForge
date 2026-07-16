from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Mapping

import httpx
from pydantic import BaseModel

from app.config import settings
from resume_evidence import DEFAULT_EVIDENCE_PATHS, ProjectsFile, SkillsFile
from resume_generation.config import (
    DEFAULT_GENERATION_CONFIG_PATH,
    DEFAULT_JOB_TARGET_PATH,
)
from resume_generation.cache import ResumeGenerationStageCache
from resume_generation.models import (
    JobTarget,
    ProjectSelectionResult,
    ResumeGenerationConfig,
    ResumeSelectionContext,
    SkillSelectionResult,
)
from resume_generation.token_usage import (
    ResumeGenerationTokenUsageMonitor,
    extract_response_token_usage,
)


logger = logging.getLogger("resume_generation")
SKILL_CATEGORIES = ("technology", "programming", "concepts")
SELECTION_CACHE_IGNORED_FIELDS = {"top_n", "dev_mode", "llm_max_output_tokens"}


class ResumeGenerationError(RuntimeError):
    """Raised when the generation orchestration cannot complete."""


def _exclude_none(data: BaseModel) -> dict[str, Any]:
    return data.model_dump(exclude_none=True)


def _selection_cache_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key not in SELECTION_CACHE_IGNORED_FIELDS
    }


def _skill_selection_full_top_n(payload: dict[str, Any]) -> int:
    counts = []
    for category in SKILL_CATEGORIES:
        category_values = payload.get(category)
        counts.append(len(category_values) if isinstance(category_values, list) else 0)
    return max(counts, default=0)


def _project_selection_full_top_n(payload: dict[str, Any]) -> int:
    candidates = payload.get("candidates")
    return len(candidates) if isinstance(candidates, list) else 0


def _canonical_selection_fetch_payload(
    payload: dict[str, Any],
    *,
    full_top_n: int,
) -> dict[str, Any]:
    fetch_payload = dict(payload)
    fetch_payload["top_n"] = full_top_n
    fetch_payload["dev_mode"] = True
    return fetch_payload


def _slice_for_top_n(values: Any, top_n: int | None) -> Any:
    if not isinstance(values, list):
        return values
    if top_n is None:
        return list(values)
    return list(values[:top_n])


def _payload_top_n(payload: dict[str, Any], default: int | None) -> int | None:
    value = payload.get("top_n", default)
    return value if value is None or isinstance(value, int) else default


def _payload_dev_mode(payload: dict[str, Any]) -> bool:
    value = payload.get("dev_mode", settings.DEV_MODE)
    return bool(value)


def _shape_skill_selection_response(
    response_data: dict[str, Any],
    *,
    payload: dict[str, Any],
) -> dict[str, Any]:
    top_n = _payload_top_n(payload, settings.SKILL_TOP_N)
    shaped = {
        category: _slice_for_top_n(response_data.get(category, []), top_n)
        for category in SKILL_CATEGORIES
    }

    if _payload_dev_mode(payload):
        details = response_data.get("details")
        if details is not None:
            shaped["details"] = details

    return shaped


def _shape_project_selection_response(
    response_data: dict[str, Any],
    *,
    payload: dict[str, Any],
) -> dict[str, Any]:
    top_n = _payload_top_n(payload, settings.PROJ_TOP_N)
    ranked_projects = _slice_for_top_n(response_data.get("ranked_projects", []), top_n)

    selected_project_ids: list[str] = []
    if isinstance(ranked_projects, list):
        for project in ranked_projects:
            if isinstance(project, dict) and isinstance(project.get("project_id"), str):
                selected_project_ids.append(project["project_id"])
    else:
        raw_project_ids = response_data.get("selected_project_ids", [])
        if isinstance(raw_project_ids, list):
            selected_project_ids = raw_project_ids

    shaped: dict[str, Any] = {
        "selected_project_ids": selected_project_ids,
        "ranked_projects": ranked_projects,
    }

    if _payload_dev_mode(payload):
        details = response_data.get("details")
        if details is not None:
            shaped["details"] = details

    return shaped


def build_skill_selection_payload(
    *,
    job_target: JobTarget,
    skills_file: SkillsFile,
    config: ResumeGenerationConfig,
) -> dict[str, Any]:
    payload = {
        "job_role": job_target.title,
        "job_text": job_target.description,
        **skills_file.skills.model_dump(),
        **_exclude_none(config.skill_selection),
    }
    return {key: value for key, value in payload.items() if value is not None}


def _project_selection_payload(
    *,
    job_target: JobTarget,
    projects_file: ProjectsFile,
    config: ResumeGenerationConfig,
) -> dict[str, Any]:
    candidates = [
        {
            "id": project.id,
            "name": project.name,
            "summary": project.summary,
            "skills": project.skills.model_dump(),
        }
        for project in projects_file.iter_projects()
        if project.active
    ]
    payload = {
        "context": {
            "title": job_target.title,
            "description": job_target.description,
        },
        "candidates": candidates,
        **_exclude_none(config.project_selection),
    }
    return {key: value for key, value in payload.items() if value is not None}


def _post_json(
    client: httpx.Client,
    endpoint: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    try:
        response = client.post(endpoint, json=payload)
    except httpx.HTTPError as exc:
        raise ResumeGenerationError(f"HTTP request to {endpoint} failed: {exc}") from exc

    if response.status_code >= 400:
        raise ResumeGenerationError(
            f"HTTP request to {endpoint} returned {response.status_code}: {response.text}"
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise ResumeGenerationError(f"HTTP response from {endpoint} was not valid JSON") from exc

    if not isinstance(data, dict):
        raise ResumeGenerationError(f"HTTP response from {endpoint} must be a JSON object")
    return data


def _should_cache_stage_response(
    *,
    stage: str,
    response_data: dict[str, Any],
) -> bool:
    if stage not in {"skill_selection", "project_selection"}:
        return True

    details = response_data.get("details")
    if not isinstance(details, dict):
        return True

    if details.get("_fallback_method") == "baseline":
        return False

    llm_metadata = details.get("_llm")
    if isinstance(llm_metadata, dict) and llm_metadata.get("fallback") == "baseline":
        return False

    project_llm_metadata = details.get("_project_llm")
    if (
        isinstance(project_llm_metadata, dict)
        and project_llm_metadata.get("fallback") == "baseline"
    ):
        return False

    return True


def _cached_post_json(
    *,
    cache: ResumeGenerationStageCache | None,
    stage: str,
    client: httpx.Client,
    endpoint: str,
    payload: dict[str, Any],
    cache_payload: dict[str, Any] | None = None,
    fetch_payload: dict[str, Any] | None = None,
    namespace: str | None = None,
    should_use_cached: Callable[[dict[str, Any]], bool] | None = None,
    token_usage_monitor: ResumeGenerationTokenUsageMonitor | None = None,
    stage_response_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if cache is None:
        data = _post_json(client, endpoint, payload)
        token_usage = extract_response_token_usage(stage, data)
        if token_usage_monitor is not None:
            token_usage_monitor.observe(stage, token_usage)
        record = {
            "stage": stage,
            "endpoint": endpoint,
            "namespace": namespace,
            "source": "http",
            "cache_status": "disabled",
            "cache_key": None,
            "llm_max_output_tokens": payload.get("llm_max_output_tokens"),
            **token_usage.model_dump(),
        }
        if stage_response_records is not None:
            stage_response_records.append(record)
        logger.info(
            "resume_generation_stage_response",
            extra={
                "event": "resume_generation_stage_response",
                **record,
            },
        )
        return data

    request_payload = fetch_payload if fetch_payload is not None else payload
    result = cache.get_or_store_result(
        stage=stage,
        payload=request_payload,
        cache_payload=cache_payload,
        namespace=namespace,
        should_use_cached=should_use_cached,
        fetch=lambda: _post_json(client, endpoint, request_payload),
        should_store=lambda data: _should_cache_stage_response(
            stage=stage,
            response_data=data,
        ),
    )
    token_usage = extract_response_token_usage(stage, result.data)
    if token_usage_monitor is not None:
        token_usage_monitor.observe(stage, token_usage)
    cache_status = (
        "hit"
        if result.source == "cache"
        else "skipped"
        if not result.stored
        else "refresh"
        if cache.force_refresh
        else "miss"
    )
    record = {
        "stage": stage,
        "endpoint": endpoint,
        "namespace": namespace,
        "source": result.source,
        "cache_status": cache_status,
        "cache_key": result.cache_key,
        "llm_max_output_tokens": payload.get("llm_max_output_tokens"),
        **token_usage.model_dump(),
    }
    if stage_response_records is not None:
        stage_response_records.append(record)
    logger.info(
        "resume_generation_stage_response",
        extra={
            "event": "resume_generation_stage_response",
            **record,
        },
    )
    return result.data


def generate_selection_context(
    *,
    loaded_evidence: Mapping[str, BaseModel],
    config: ResumeGenerationConfig,
    job_target: JobTarget,
    config_path: Path | str = DEFAULT_GENERATION_CONFIG_PATH,
    job_target_path: Path | str = DEFAULT_JOB_TARGET_PATH,
    evidence_paths: Mapping[str, Path | str] | None = None,
    cache: ResumeGenerationStageCache | None = None,
    token_usage_monitor: ResumeGenerationTokenUsageMonitor | None = None,
    stage_response_records: list[dict[str, Any]] | None = None,
) -> ResumeSelectionContext:
    merged_evidence_paths = dict(DEFAULT_EVIDENCE_PATHS)
    if evidence_paths is not None:
        merged_evidence_paths.update(
            {schema_name: Path(path) for schema_name, path in evidence_paths.items()}
        )

    projects_file = loaded_evidence.get("projects")
    skills_file = loaded_evidence.get("skills")
    if not isinstance(projects_file, ProjectsFile):
        raise ResumeGenerationError("Loaded evidence did not include a valid projects file")
    if not isinstance(skills_file, SkillsFile):
        raise ResumeGenerationError("Loaded evidence did not include a valid skills file")

    with httpx.Client(
        base_url=config.app.base_url,
        timeout=config.app.timeout_seconds,
    ) as client:
        skill_payload = build_skill_selection_payload(
            job_target=job_target,
            skills_file=skills_file,
            config=config,
        )
        skill_cache_payload = _selection_cache_payload(skill_payload)
        skill_fetch_payload = _canonical_selection_fetch_payload(
            skill_payload,
            full_top_n=_skill_selection_full_top_n(skill_payload),
        )
        skill_response = _cached_post_json(
            cache=cache,
            stage="skill_selection",
            client=client,
            endpoint="/select-skills",
            payload=skill_payload,
            cache_payload=skill_cache_payload,
            fetch_payload=skill_fetch_payload,
            token_usage_monitor=token_usage_monitor,
            stage_response_records=stage_response_records,
        )
        if cache is not None:
            skill_response = _shape_skill_selection_response(
                skill_response,
                payload=skill_payload,
            )

        project_payload = _project_selection_payload(
            job_target=job_target,
            projects_file=projects_file,
            config=config,
        )
        project_cache_payload = _selection_cache_payload(project_payload)
        project_fetch_payload = _canonical_selection_fetch_payload(
            project_payload,
            full_top_n=_project_selection_full_top_n(project_payload),
        )
        project_response = _cached_post_json(
            cache=cache,
            stage="project_selection",
            client=client,
            endpoint="/select-projects",
            payload=project_payload,
            cache_payload=project_cache_payload,
            fetch_payload=project_fetch_payload,
            token_usage_monitor=token_usage_monitor,
            stage_response_records=stage_response_records,
        )
        if cache is not None:
            project_response = _shape_project_selection_response(
                project_response,
                payload=project_payload,
            )

    project_selection = ProjectSelectionResult.model_validate(project_response)
    projects_by_id = projects_file.projects_by_id()
    selected_projects = [
        projects_by_id[project_id]
        for project_id in project_selection.selected_project_ids
        if project_id in projects_by_id
    ]

    return ResumeSelectionContext(
        job_target=job_target,
        selected_skills=SkillSelectionResult.model_validate(skill_response),
        project_selection=project_selection,
        selected_projects=selected_projects,
        config_path=Path(config_path),
        job_target_path=Path(job_target_path),
        evidence_paths=merged_evidence_paths,
    )
