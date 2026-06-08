# entry point for resume generation

from pathlib import Path

from resume_evidence import load_registered_evidence
from resume_generation.config import (
    DEFAULT_GENERATION_CONFIG_PATH,
    DEFAULT_JOB_TARGET_PATH,
    load_generation_config,
    load_job_target,
)
from resume_generation.bullet_points import generate_project_bullet_points
from resume_generation.models import ProjectBulletPointResult
from resume_generation.selection import generate_selection_context


def run_resume_generation_pipeline(
    *,
    config_path: Path | str = DEFAULT_GENERATION_CONFIG_PATH,
    job_target_path: Path | str = DEFAULT_JOB_TARGET_PATH,
    evidence_paths: dict[str, Path | str] | None = None,
) -> list[ProjectBulletPointResult]:
    config = load_generation_config(config_path)
    job_target = load_job_target(job_target_path)
    loaded_evidence = load_registered_evidence(evidence_paths)

    context = generate_selection_context(
        loaded_evidence=loaded_evidence,
        config=config,
        job_target=job_target,
        config_path=config_path,
        job_target_path=job_target_path,
        evidence_paths=evidence_paths,
    )

    # TODO: load basic user info (name, contact info, etc)

    # TODO: other info like experience, publications etc. will come in the future

    # selection context includes skills and projects ranked by relevance to the job target.

    # TODO: optionally re-rank project skills with LLM (not the skills themselves), this is ranked per project, priortizing skills that are more relevant to the job target. This should be done with a separate reranking API instead of the one used for regular skill ranking

    # TODO: bullet point generation. Call the "/generate-bulletpoints" API with the project records
    bullet_points = generate_project_bullet_points(
        selected_projects=context.selected_projects,
        config=config,
        job_target=job_target,
    )

    # TODO: optionally overall content validation

    # TODO: generation step, using the results to generate a working resume draft schema, this will be used to generate the actual resume content in the future

    # TODO: output LaTeX format resume, this is the final output for now, but in the future we can also output other formats like PDF, Word, etc.

    return bullet_points


if __name__ == "__main__":
    run_resume_generation_pipeline()
