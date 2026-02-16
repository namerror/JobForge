from fastapi import FastAPI
from app.models import SkillSelectRequest, SkillSelectResponse
from app.scoring.baseline import baseline_select_skills

app = FastAPI(title="Skill Relevance Selector")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/select-skills", response_model=SkillSelectResponse)
def select_skills(payload: SkillSelectRequest):
    selected_skills, details = baseline_select_skills(payload)
    return SkillSelectResponse(
        technology=selected_skills.get("technology", []),
        programming=selected_skills.get("programming", []),
        concepts=selected_skills.get("concepts", []),
        details=details
    )