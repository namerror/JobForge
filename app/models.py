from pydantic import BaseModel
from typing import List, Dict

class SkillSelectRequest(BaseModel):
    job_role: str
    technology: List[str]
    programming: List[str]
    concepts: List[str]

class SkillSelectResponse(BaseModel):
    technology: List[str]
    programming: List[str]
    concepts: List[str]