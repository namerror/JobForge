from __future__ import annotations

from collections.abc import Iterable

from resume_evidence.models import (
    EducationFile,
    ExperienceFile,
    ProjectRecord,
    ProjectSkills,
    UserInfoFile,
)
from resume_generation.models import (
    IntermediateResumeResult,
    ProjectBulletPointResult,
    ResumeEducationItem,
    ResumeExperienceItem,
    ResumeProjectItem,
    ResumeSelectionContext,
    ResumeSkillsSection,
    ResumeTopSection,
)


def assemble_intermediate_resume_result(
    *,
    user_info: UserInfoFile,
    education: EducationFile,
    experience: ExperienceFile,
    selection_context: ResumeSelectionContext,
    selected_projects: Iterable[ProjectRecord],
    project_bullet_points: Iterable[ProjectBulletPointResult],
) -> IntermediateResumeResult:
    bullet_points_by_project_id = {
        result.project_id: result.bullet_points for result in project_bullet_points
    }

    return IntermediateResumeResult(
        top=ResumeTopSection(
            name=user_info.name,
            phone=user_info.phone,
            email=user_info.email,
            github=user_info.github,
            website=user_info.website,
            linkedin=user_info.linkedin,
        ),
        education=[
            ResumeEducationItem(
                name=item.name,
                degree=item.degree,
                grade=item.grade,
                start=item.start,
                end=item.end,
                location=item.location,
                relevant_coursework=item.relevant_coursework,
            )
            for item in education.education
        ],
        experience=[
            ResumeExperienceItem(
                name=item.name,
                bullet_points=item.highlights,
                skills=_flatten_skills(item.skills),
                location=item.location,
                start=item.start,
                end=item.end,
            )
            for item in experience.experience
            if item.active
        ],
        projects=[
            ResumeProjectItem(
                name=project.name,
                bullet_points=bullet_points_by_project_id.get(project.id, []),
                skills=_flatten_skills(project.skills),
                links=project.links or [],
            )
            for project in selected_projects
        ],
        skills=ResumeSkillsSection(
            technology=selection_context.selected_skills.technology,
            programming=selection_context.selected_skills.programming,
            concepts=selection_context.selected_skills.concepts,
        ),
    )


def _flatten_skills(skills: ProjectSkills) -> list[str]:
    return [*skills.technology, *skills.programming, *skills.concepts]
