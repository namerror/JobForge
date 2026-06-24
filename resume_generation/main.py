# entry point for resume generation

import logging
import os
from pathlib import Path

from resume_evidence import (
    EducationFile,
    ExperienceFile,
    UserInfoFile,
    load_registered_evidence,
)
from resume_generation.config import (
    DEFAULT_GENERATION_CONFIG_PATH,
    DEFAULT_JOB_TARGET_PATH,
    load_generation_config,
    load_job_target,
)
from resume_generation.assembly import assemble_intermediate_resume_result
from resume_generation.bullet_points import (
    generate_experience_bullet_points,
    generate_project_bullet_points,
)
from resume_generation.cache import ResumeGenerationStageCache
from resume_generation.link_scanning import enrich_projects_with_link_scanning
from resume_generation.models import IntermediateResumeResult
from resume_generation.selection import generate_selection_context

_REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESUME_RESULT_ARTIFACT_PATH = (
    _REPO_ROOT / "user" / "resume_generation" / "resume_result.json"
)
logger = logging.getLogger("resume_generation")


def write_resume_result_artifact(
    resume_result: IntermediateResumeResult,
    path: Path | str = DEFAULT_RESUME_RESULT_ARTIFACT_PATH,
) -> Path:
    artifact_path = Path(path)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = artifact_path.with_suffix(artifact_path.suffix + ".tmp")
    tmp_path.write_text(
        resume_result.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp_path, artifact_path)
    return artifact_path


def run_resume_generation_pipeline(
    *,
    config_path: Path | str = DEFAULT_GENERATION_CONFIG_PATH,
    job_target_path: Path | str = DEFAULT_JOB_TARGET_PATH,
    evidence_paths: dict[str, Path | str] | None = None,
    resume_result_artifact_path: Path | str = DEFAULT_RESUME_RESULT_ARTIFACT_PATH,
) -> None:
    logger.info(
        "resume_generation_pipeline_start",
        extra={
            "event": "resume_generation_pipeline_start",
            "config_path": str(config_path),
            "job_target_path": str(job_target_path),
        },
    )
    config = load_generation_config(config_path)
    job_target = load_job_target(job_target_path)
    loaded_evidence = load_registered_evidence(evidence_paths)
    cache = ResumeGenerationStageCache.from_config(
        config.cache,
        config_path=config_path,
    )

    _user_info = loaded_evidence.get("user")
    if not isinstance(_user_info, UserInfoFile):
        raise TypeError("Loaded evidence did not include a valid user info file")

    _education = loaded_evidence.get("education")
    if not isinstance(_education, EducationFile):
        raise TypeError("Loaded evidence did not include a valid education file")

    _experience = loaded_evidence.get("experience")
    if not isinstance(_experience, ExperienceFile):
        raise TypeError("Loaded evidence did not include a valid experience file")

    logger.info(
        "resume_generation_stage_start",
        extra={"event": "resume_generation_stage_start", "stage": "selection"},
    )
    # selection context includes skills and projects ranked by relevance to the job target.
    context = generate_selection_context(
        loaded_evidence=loaded_evidence,
        config=config,
        job_target=job_target,
        config_path=config_path,
        job_target_path=job_target_path,
        evidence_paths=evidence_paths,
        cache=cache,
    )
    logger.info(
        "resume_generation_stage_complete",
        extra={
            "event": "resume_generation_stage_complete",
            "stage": "selection",
            "selected_project_count": len(context.selected_projects),
        },
    )

    # TODO: other info like publications etc. will come in the future

    # TODO: optionally re-rank project skills with LLM (not the skills themselves), this is ranked per project, priortizing skills that are more relevant to the job target. This should be done with a separate reranking API instead of the one used for regular skill ranking

    link_stage_extra = {
        "event": "resume_generation_stage_start",
        "stage": "link_scanning",
        "enabled": config.link_scanning.enabled,
        "project_count": len(context.selected_projects),
    }
    if config.link_scanning.enabled:
        logger.info("resume_generation_stage_start", extra=link_stage_extra)
    else:
        logger.info(
            "resume_generation_stage_skipped",
            extra={
                "event": "resume_generation_stage_skipped",
                "stage": "link_scanning",
                "reason": "disabled",
            },
        )
    enriched_projects = enrich_projects_with_link_scanning(
        selected_projects=context.selected_projects,
        config=config,
        job_target=job_target,
        cache=cache,
    )
    if config.link_scanning.enabled:
        logger.info(
            "resume_generation_stage_complete",
            extra={
                "event": "resume_generation_stage_complete",
                "stage": "link_scanning",
                "project_count": len(enriched_projects),
            },
        )

    logger.info(
        "resume_generation_stage_start",
        extra={
            "event": "resume_generation_stage_start",
            "stage": "project_bullet_points",
            "project_count": len(enriched_projects),
        },
    )
    bullet_points = generate_project_bullet_points(
        selected_projects=enriched_projects,
        config=config,
        job_target=job_target,
        cache=cache,
    )
    logger.info(
        "resume_generation_stage_complete",
        extra={
            "event": "resume_generation_stage_complete",
            "stage": "project_bullet_points",
            "result_count": len(bullet_points),
        },
    )

    active_experience_count = sum(1 for item in _experience.experience if item.active)
    logger.info(
        "resume_generation_stage_start",
        extra={
            "event": "resume_generation_stage_start",
            "stage": "experience_bullet_points",
            "experience_count": active_experience_count,
        },
    )
    experience_bullet_points = generate_experience_bullet_points(
        experience=_experience.experience,
        config=config,
        job_target=job_target,
        cache=cache,
    )
    logger.info(
        "resume_generation_stage_complete",
        extra={
            "event": "resume_generation_stage_complete",
            "stage": "experience_bullet_points",
            "result_count": len(experience_bullet_points),
        },
    )

    # TODO: optionally overall content validation

    logger.info(
        "resume_generation_stage_start",
        extra={"event": "resume_generation_stage_start", "stage": "assembly"},
    )
    resume_result = assemble_intermediate_resume_result(
        user_info=_user_info,
        education=_education,
        experience=_experience,
        selection_context=context,
        selected_projects=enriched_projects,
        project_bullet_points=bullet_points,
        experience_bullet_points=experience_bullet_points,
    )
    logger.info(
        "resume_generation_stage_complete",
        extra={"event": "resume_generation_stage_complete", "stage": "assembly"},
    )

    artifact_path = write_resume_result_artifact(resume_result, resume_result_artifact_path)
    logger.info(
        "resume_generation_artifact_written",
        extra={
            "event": "resume_generation_artifact_written",
            "path": str(artifact_path),
        },
    )

    # TODO: output LaTeX format resume, this is the final output for now, but in the future we can also output other formats like PDF, Word, etc.

    logger.info(
        "resume_generation_pipeline_complete",
        extra={"event": "resume_generation_pipeline_complete"},
    )
    return None


if __name__ == "__main__":
    run_resume_generation_pipeline()
