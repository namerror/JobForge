from pydantic import BaseModel
from typing import List, Dict

class SkillSelectRequest(BaseModel):
    job_role: str
    technology: List[str]
    programming: List[str]
    concepts: List[str]
    job_text: str | None = None  # Optional full job description text for context
    top_n: int | None = None  # Optional override for how many skills to select per category
    method: str | None = None  # Optional override for selection method (e.g., "baseline", "embeddings", "hybrid")
    dev_mode: bool | None = None  # Optional override for whether to include dev-only

class SkillSelectResponse(BaseModel):
    technology: List[str]
    programming: List[str]
    concepts: List[str]
    details: Dict[str, Dict] | None = None  # Optional field for dev mode