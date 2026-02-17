from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from app.models import SkillSelectRequest, SkillSelectResponse
from app.config import settings
from app.services.skill_selector import select_skills_service
from app.metrics import metrics
from app.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.LOG_LEVEL)
    yield


app = FastAPI(title="Skill Relevance Selector", lifespan=lifespan)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "0.2.0",
        "method": settings.METHOD,
        "top_n": settings.TOP_N,
        "dev_mode": settings.DEV_MODE,
        }

@app.get("/metrics-lite")
def get_metrics():
    return {
        "requests_total": metrics.requests_total,
        "errors_total": metrics.errors_total,
        "avg_latency_ms": round(metrics.avg_latency_ms(), 3),
        "method_usage": metrics.method_usage,
    }

@app.post("/select-skills", response_model=SkillSelectResponse)
def select_skills(payload: SkillSelectRequest) -> SkillSelectResponse:
    try:
        return select_skills_service(payload)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))