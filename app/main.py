from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from app import __version__
from pydantic import ValidationError

from app.skill_selection.models import SkillSelectRequest, SkillSelectResponse
from app.config import settings
from app.skill_selection.selector import select_skills_service
from app.metrics import metrics
from app.logging_config import setup_logging
from app.project_selection.models import ProjectSelectRequest, ProjectSelectionResult
from app.project_selection.service import record_project_selection_error, select_projects_service
from app.resume_evidence import load_registered_evidence


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.LOG_LEVEL)
    app.state.resume_evidence = load_registered_evidence()
    yield


app = FastAPI(title="JobForge Resume Engine", lifespan=lifespan)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": __version__,
        "service": "jobforge-resume-engine",
        "method": settings.METHOD,
        "top_n": settings.TOP_N,
        "baseline_filter": settings.BASELINE_FILTER,
        "dev_mode": settings.DEV_MODE,
    }


@app.get("/metrics-lite")
async def get_metrics():
    return {
        "requests_total": metrics.requests_total,
        "errors_total": metrics.errors_total,
        "total_tokens": metrics.total_tokens,
        "avg_latency_ms": round(metrics.avg_latency_ms(), 3),
        "method_usage": metrics.method_usage,
        "subsystems": metrics.subsystem_snapshots(),
    }


@app.post("/select-skills", response_model=SkillSelectResponse)
async def select_skills(payload: SkillSelectRequest) -> SkillSelectResponse:
    try:
        return select_skills_service(payload)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@app.post("/select-projects", response_model=ProjectSelectionResult)
async def select_projects(payload: dict[str, Any]) -> ProjectSelectionResult:
    try:
        request = ProjectSelectRequest.model_validate(payload)
        return select_projects_service(request)
    except ValidationError as ve:
        method = payload.get("method") if isinstance(payload, dict) else None
        record_project_selection_error(method if isinstance(method, str) else "invalid")
        raise HTTPException(status_code=400, detail=str(ve))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
