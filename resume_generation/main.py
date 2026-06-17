# entry point for resume generation

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
from resume_generation.bullet_points import generate_project_bullet_points
from resume_generation.link_scanning import enrich_projects_with_link_scanning
from resume_generation.selection import generate_selection_context


def run_resume_generation_pipeline(
    *,
    config_path: Path | str = DEFAULT_GENERATION_CONFIG_PATH,
    job_target_path: Path | str = DEFAULT_JOB_TARGET_PATH,
    evidence_paths: dict[str, Path | str] | None = None,
) -> None:
    config = load_generation_config(config_path)
    job_target = load_job_target(job_target_path)
    loaded_evidence = load_registered_evidence(evidence_paths)

    _user_info = loaded_evidence.get("user")
    if not isinstance(_user_info, UserInfoFile):
        raise TypeError("Loaded evidence did not include a valid user info file")

    _education = loaded_evidence.get("education")
    if not isinstance(_education, EducationFile):
        raise TypeError("Loaded evidence did not include a valid education file")

    _experience = loaded_evidence.get("experience")
    if not isinstance(_experience, ExperienceFile):
        raise TypeError("Loaded evidence did not include a valid experience file")

    # selection context includes skills and projects ranked by relevance to the job target.
    context = generate_selection_context(
        loaded_evidence=loaded_evidence,
        config=config,
        job_target=job_target,
        config_path=config_path,
        job_target_path=job_target_path,
        evidence_paths=evidence_paths,
    )

    # TODO: other info like publications etc. will come in the future

    # TODO: optionally re-rank project skills with LLM (not the skills themselves), this is ranked per project, priortizing skills that are more relevant to the job target. This should be done with a separate reranking API instead of the one used for regular skill ranking

    enriched_projects = enrich_projects_with_link_scanning(
        selected_projects=context.selected_projects,
        config=config,
        job_target=job_target,
    )

    bullet_points = generate_project_bullet_points(
        selected_projects=enriched_projects,
        config=config,
        job_target=job_target,
    )

    # TODO: optionally overall content validation

    resume_result = assemble_intermediate_resume_result(
        user_info=_user_info,
        education=_education,
        experience=_experience,
        selection_context=context,
        selected_projects=enriched_projects,
        project_bullet_points=bullet_points,
    )

    # TODO: output LaTeX format resume, this is the final output for now, but in the future we can also output other formats like PDF, Word, etc.

    return None


if __name__ == "__main__":
    run_resume_generation_pipeline()
