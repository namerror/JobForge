from fastapi import FastAPI
from app.models import SkillSelectRequest, SkillSelectResponse

app = FastAPI(title="Skill Relevance Selector")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/select-skills", response_model=SkillSelectResponse)
def select_skills(payload: SkillSelectRequest):
    # Placeholder logic — will be replaced by baseline scorer
    return SkillSelectResponse(
        technology=payload.technology,
        programming=payload.programming,
        concepts=payload.concepts,
    )