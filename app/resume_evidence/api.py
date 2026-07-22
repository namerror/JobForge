from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

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
from app.resume_evidence.service import (
    EvidenceNotFoundError,
    create_education,
    create_experience,
    create_project,
    delete_education,
    delete_experience,
    delete_project,
    get_education,
    get_experience,
    get_project,
    load_education,
    load_experience,
    load_projects,
    load_resume_evidence_registry,
    load_skills,
    load_user_info,
    update_education,
    update_experience,
    update_project,
    update_skills,
    update_user_info,
)

router = APIRouter(prefix="/resume-evidence", tags=["resume-evidence"])


@router.get("", response_model=ResumeEvidenceRegistry)
async def get_resume_evidence(request: Request) -> ResumeEvidenceRegistry:
    try:
        registry = load_resume_evidence_registry()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    request.app.state.resume_evidence = {
        "education": registry.education,
        "experience": registry.experience,
        "projects": registry.projects,
        "skills": registry.skills,
        "user": registry.user,
    }
    return registry


@router.get("/projects", response_model=ProjectsFile)
async def list_projects() -> ProjectsFile:
    try:
        return load_projects()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/projects",
    response_model=ProjectRecord,
    status_code=status.HTTP_201_CREATED,
)
async def post_project(request: Request, payload: ProjectRecordInput) -> ProjectRecord:
    try:
        created, projects = create_project(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _store_evidence_state(request, "projects", projects)
    return created


@router.get("/projects/{project_id}", response_model=ProjectRecord)
async def read_project(project_id: str) -> ProjectRecord:
    try:
        return get_project(project_id)
    except EvidenceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/projects/{project_id}", response_model=ProjectRecord)
async def put_project(
    request: Request,
    project_id: str,
    payload: ProjectRecordInput,
) -> ProjectRecord:
    try:
        updated, projects = update_project(project_id, payload)
    except EvidenceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _store_evidence_state(request, "projects", projects)
    return updated


@router.delete("/projects/{project_id}", response_model=ProjectRecord)
async def remove_project(request: Request, project_id: str) -> ProjectRecord:
    try:
        deleted, projects = delete_project(project_id)
    except EvidenceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _store_evidence_state(request, "projects", projects)
    return deleted


@router.get("/experience", response_model=ExperienceFile)
async def list_experience() -> ExperienceFile:
    try:
        return load_experience()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/experience",
    response_model=ExperienceRecord,
    status_code=status.HTTP_201_CREATED,
)
async def post_experience(
    request: Request,
    payload: ExperienceRecordInput,
) -> ExperienceRecord:
    try:
        created, experience = create_experience(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _store_evidence_state(request, "experience", experience)
    return created


@router.get("/experience/{experience_id}", response_model=ExperienceRecord)
async def read_experience(experience_id: str) -> ExperienceRecord:
    try:
        return get_experience(experience_id)
    except EvidenceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/experience/{experience_id}", response_model=ExperienceRecord)
async def put_experience(
    request: Request,
    experience_id: str,
    payload: ExperienceRecordInput,
) -> ExperienceRecord:
    try:
        updated, experience = update_experience(experience_id, payload)
    except EvidenceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _store_evidence_state(request, "experience", experience)
    return updated


@router.delete("/experience/{experience_id}", response_model=ExperienceRecord)
async def remove_experience(request: Request, experience_id: str) -> ExperienceRecord:
    try:
        deleted, experience = delete_experience(experience_id)
    except EvidenceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _store_evidence_state(request, "experience", experience)
    return deleted


@router.get("/education", response_model=EducationFile)
async def list_education() -> EducationFile:
    try:
        return load_education()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/education",
    response_model=EducationRecord,
    status_code=status.HTTP_201_CREATED,
)
async def post_education(
    request: Request,
    payload: EducationRecordInput,
) -> EducationRecord:
    try:
        created, education = create_education(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _store_evidence_state(request, "education", education)
    return created


@router.get("/education/{education_id}", response_model=EducationRecord)
async def read_education(education_id: str) -> EducationRecord:
    try:
        return get_education(education_id)
    except EvidenceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/education/{education_id}", response_model=EducationRecord)
async def put_education(
    request: Request,
    education_id: str,
    payload: EducationRecordInput,
) -> EducationRecord:
    try:
        updated, education = update_education(education_id, payload)
    except EvidenceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _store_evidence_state(request, "education", education)
    return updated


@router.delete("/education/{education_id}", response_model=EducationRecord)
async def remove_education(request: Request, education_id: str) -> EducationRecord:
    try:
        deleted, education = delete_education(education_id)
    except EvidenceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _store_evidence_state(request, "education", education)
    return deleted


@router.get("/skills", response_model=SkillsFile)
async def read_skills() -> SkillsFile:
    try:
        return load_skills()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/skills", response_model=SkillsFile)
async def put_skills(request: Request, payload: SkillsInput) -> SkillsFile:
    try:
        updated = update_skills(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _store_evidence_state(request, "skills", updated)
    return updated


@router.get("/user", response_model=UserInfoFile)
async def read_user_info() -> UserInfoFile:
    try:
        return load_user_info()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/user", response_model=UserInfoFile)
async def put_user_info(request: Request, payload: UserInfoInput) -> UserInfoFile:
    try:
        updated = update_user_info(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _store_evidence_state(request, "user", updated)
    return updated


def _store_evidence_state(request: Request, schema_name: str, evidence: BaseModel) -> None:
    current_state = getattr(request.app.state, "resume_evidence", {})
    if not isinstance(current_state, dict):
        current_state = {}
    updated_state = dict(current_state)
    updated_state[schema_name] = evidence.model_copy(deep=True)
    request.app.state.resume_evidence = updated_state
