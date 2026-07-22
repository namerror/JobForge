from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from app.resume_evidence.loader import load_registered_evidence
from app.resume_evidence.models import (
    EducationFile,
    EducationRecord,
    EducationRecordInput,
    ExperienceFile,
    ExperienceRecord,
    ExperienceRecordInput,
    ProjectRecord,
    ProjectRecordInput,
    ProjectsFile,
    ResumeEvidenceRegistry,
    SkillsFile,
    SkillsInput,
    UserInfoFile,
    UserInfoInput,
)
from app.resume_evidence.session import (
    EducationEvidenceSession,
    ExperienceEvidenceSession,
    ProjectsEvidenceSession,
    SkillsEvidenceSession,
    UserInfoEvidenceSession,
)


class EvidenceNotFoundError(ValueError):
    pass


RecordT = TypeVar("RecordT", bound=BaseModel)


def load_resume_evidence_registry() -> ResumeEvidenceRegistry:
    loaded = load_registered_evidence()
    return ResumeEvidenceRegistry.model_validate(loaded)


def load_projects() -> ProjectsFile:
    return ProjectsEvidenceSession.load().baseline


def load_experience() -> ExperienceFile:
    return ExperienceEvidenceSession.load().baseline


def load_education() -> EducationFile:
    return EducationEvidenceSession.load().baseline


def load_skills() -> SkillsFile:
    return SkillsEvidenceSession.load().baseline


def load_user_info() -> UserInfoFile:
    return UserInfoEvidenceSession.load().baseline


def get_project(project_id: str) -> ProjectRecord:
    return _get_record_by_id(load_projects().projects, project_id, "project")


def create_project(payload: ProjectRecordInput) -> tuple[ProjectRecord, ProjectsFile]:
    session = ProjectsEvidenceSession.load()
    created = session.create_project(
        name=payload.name,
        summary=payload.summary,
        highlights=payload.highlights,
        active=payload.active,
        technology=payload.skills.technology,
        programming=payload.skills.programming,
        concepts=payload.skills.concepts,
        links=payload.links,
    )
    session.apply()
    return created, session.baseline


def update_project(
    project_id: str,
    payload: ProjectRecordInput,
) -> tuple[ProjectRecord, ProjectsFile]:
    session = ProjectsEvidenceSession.load()
    index = _get_record_index_by_id(session.staged.projects, project_id, "project")
    updated = session.update_project(
        index,
        name=payload.name,
        summary=payload.summary,
        highlights=payload.highlights,
        active=payload.active,
        technology=payload.skills.technology,
        programming=payload.skills.programming,
        concepts=payload.skills.concepts,
        links=payload.links,
    )
    session.apply()
    return updated, session.baseline


def delete_project(project_id: str) -> tuple[ProjectRecord, ProjectsFile]:
    session = ProjectsEvidenceSession.load()
    index = _get_record_index_by_id(session.staged.projects, project_id, "project")
    deleted = session.delete_project(index)
    session.apply()
    return deleted, session.baseline


def get_experience(experience_id: str) -> ExperienceRecord:
    return _get_record_by_id(load_experience().experience, experience_id, "experience")


def create_experience(payload: ExperienceRecordInput) -> tuple[ExperienceRecord, ExperienceFile]:
    session = ExperienceEvidenceSession.load()
    created = session.create_experience(
        name=payload.name,
        role=payload.role,
        summary=payload.summary,
        highlights=payload.highlights,
        active=payload.active,
        technology=payload.skills.technology,
        programming=payload.skills.programming,
        concepts=payload.skills.concepts,
        location=payload.location,
        start=payload.start,
        end=payload.end,
        links=payload.links,
    )
    session.apply()
    return created, session.baseline


def update_experience(
    experience_id: str,
    payload: ExperienceRecordInput,
) -> tuple[ExperienceRecord, ExperienceFile]:
    session = ExperienceEvidenceSession.load()
    index = _get_record_index_by_id(session.staged.experience, experience_id, "experience")
    updated = session.update_experience(
        index,
        name=payload.name,
        role=payload.role,
        summary=payload.summary,
        highlights=payload.highlights,
        active=payload.active,
        technology=payload.skills.technology,
        programming=payload.skills.programming,
        concepts=payload.skills.concepts,
        location=payload.location,
        start=payload.start,
        end=payload.end,
        links=payload.links,
    )
    session.apply()
    return updated, session.baseline


def delete_experience(experience_id: str) -> tuple[ExperienceRecord, ExperienceFile]:
    session = ExperienceEvidenceSession.load()
    index = _get_record_index_by_id(session.staged.experience, experience_id, "experience")
    deleted = session.delete_experience(index)
    session.apply()
    return deleted, session.baseline


def get_education(education_id: str) -> EducationRecord:
    return _get_record_by_id(load_education().education, education_id, "education")


def create_education(payload: EducationRecordInput) -> tuple[EducationRecord, EducationFile]:
    session = EducationEvidenceSession.load()
    created = session.create_education(
        name=payload.name,
        degree=payload.degree,
        grade=payload.grade,
        start=payload.start,
        end=payload.end,
        location=payload.location,
        relevant_coursework=payload.relevant_coursework,
    )
    session.apply()
    return created, session.baseline


def update_education(
    education_id: str,
    payload: EducationRecordInput,
) -> tuple[EducationRecord, EducationFile]:
    session = EducationEvidenceSession.load()
    index = _get_record_index_by_id(session.staged.education, education_id, "education")
    updated = session.update_education(
        index,
        name=payload.name,
        degree=payload.degree,
        grade=payload.grade,
        start=payload.start,
        end=payload.end,
        location=payload.location,
        relevant_coursework=payload.relevant_coursework,
    )
    session.apply()
    return updated, session.baseline


def delete_education(education_id: str) -> tuple[EducationRecord, EducationFile]:
    session = EducationEvidenceSession.load()
    index = _get_record_index_by_id(session.staged.education, education_id, "education")
    deleted = session.delete_education(index)
    session.apply()
    return deleted, session.baseline


def update_skills(payload: SkillsInput) -> SkillsFile:
    session = SkillsEvidenceSession.load()
    updated = session.update_skills(
        technology=payload.skills.technology,
        programming=payload.skills.programming,
        concepts=payload.skills.concepts,
    )
    session.apply()
    return updated


def update_user_info(payload: UserInfoInput) -> UserInfoFile:
    session = UserInfoEvidenceSession.load()
    updated = session.update_user_info(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        linkedin=payload.linkedin,
        github=payload.github,
        website=payload.website,
    )
    session.apply()
    return updated


def _get_record_by_id(
    records: list[RecordT],
    record_id: str,
    record_label: str,
) -> RecordT:
    for record in records:
        if getattr(record, "id") == record_id:
            return record.model_copy(deep=True)
    raise EvidenceNotFoundError(f"{record_label} '{record_id}' was not found")


def _get_record_index_by_id(
    records: list[BaseModel],
    record_id: str,
    record_label: str,
) -> int:
    for index, record in enumerate(records, start=1):
        if getattr(record, "id") == record_id:
            return index
    raise EvidenceNotFoundError(f"{record_label} '{record_id}' was not found")
