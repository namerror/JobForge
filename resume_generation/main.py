# entry point for resume generation

from pathlib import Path
from typing import Mapping

import httpx
from pydantic import BaseModel

from resume_evidence import load_registered_evidence
from resume_evidence.models import ProjectsFile
from resume_generation.config import (
    DEFAULT_GENERATION_CONFIG_PATH,
    DEFAULT_JOB_TARGET_PATH,
    load_generation_config,
    load_job_target,
)
from resume_generation.models import ProjectBulletPointResult
from resume_generation.selection import (
    ResumeGenerationError,
    _exclude_none,
    _post_json,
    generate_selection_context,
)


def bullet_point_generation(
    *,
    loaded_evidence: Mapping[str, BaseModel],
    project_ids: list[str],
    config_path: Path | str = DEFAULT_GENERATION_CONFIG_PATH,
    job_target_path: Path | str = DEFAULT_JOB_TARGET_PATH,
) -> list[ProjectBulletPointResult]:
    config = load_generation_config(config_path)
    job_target = load_job_target(job_target_path)

    projects_file = loaded_evidence.get("projects")
    if not isinstance(projects_file, ProjectsFile):
        raise ResumeGenerationError("Loaded evidence did not include a valid projects file")

    projects_by_id = projects_file.projects_by_id()
    selected_projects = [
        projects_by_id[project_id]
        for project_id in project_ids
        if project_id in projects_by_id
    ]
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


if __name__ == "__main__":
    loaded_evidence = load_registered_evidence()
    context = generate_selection_context(loaded_evidence=loaded_evidence)
    job_target = context.job_target

    # TODO: load basic user info (name, contact info, etc)

    # TODO: other info like experience, publications etc. will come in the future

    # selection: skills and projects, both ranked by relevance to the job target.
    project_ids = context.project_selection.selected_project_ids
    skills = context.selected_skills

    # TODO: optionally re-rank project skills with LLM (not the skills themselves), this is ranked per project, priortizing skills that are more relevant to the job target. This should be done with a separate reranking API instead of the one used for regular skill ranking

    # TODO: bullet point generation. Call the "/generate-bulletpoints" API with the project records
    bullet_point_generation(loaded_evidence=loaded_evidence, project_ids=project_ids)

    # TODO: optionally overall content validation

    # TODO: generation step, using the results to generate a working resume draft schema, this will be used to generate the actual resume content in the future

    # TODO: output LaTeX format resume, this is the final output for now, but in the future we can also output other formats like PDF, Word, etc.
