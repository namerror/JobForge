import dotenv
import os
from app.scoring.synonyms import SYNONYM_TO_NORMALIZED

DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"
TOP_N = int(os.getenv("TOP_N", "10"))  # Number of top skills to return per category

def normalize_skill(skill: str) -> str:
    """Normalize skill names to a standard format."""
    s = skill.strip().lower()
    
    return SYNONYM_TO_NORMALIZED.get(s, s)


def score_skill(skill: str, role_family: str, category: str, job_text: str | None=None) -> tuple[float, dict | None]:
    """Score a skill based on its presence in the job text and its relevance to the role profile."""
    normalized_skill = normalize_skill(skill)

    from app.scoring.role_profiles import ROLE_PROFILES
    role_profile = ROLE_PROFILES.get(role_family, ROLE_PROFILES["general"])

    keywords = set(role_profile.get(category, {}).get("keywords", []))
    if "inherits" in role_profile:
        for parent_role in role_profile["inherits"]:
            parent_keywords = set(ROLE_PROFILES.get(parent_role, {}).get(category, {}).get("keywords", []))
            keywords.update(parent_keywords)

    # Exact match = 3 points, partial match = 1 point
    score = 0.0
    # Handle empty strings - they shouldn't match anything
    if normalized_skill and normalized_skill in keywords:
        score = 3.0
    elif normalized_skill and any(normalized_skill in keyword for keyword in keywords):
        score = 1.0

    return score, {"normalized_skill": normalized_skill, "matched_keywords": list(keywords)} if DEV_MODE else None

def rank_skills(skills: list[str], role_family: str, category: str, job_text: str | None=None) -> tuple[list[str], dict | None]:
    """Rank skills based on their scores."""
    scored_skills = []
    for skill in skills:
        score, details = score_skill(skill, role_family, category, job_text)
        scored_skills.append((skill, score, details))

    # Sort by score (descending) and then alphabetically
    scored_skills.sort(key=lambda x: (-x[1], x[0]))

    ranked_skills = [skill for skill, score, details in scored_skills]
    details_dict = {skill: {"score": score, **details} for skill, score, details in scored_skills}

    return ranked_skills[:TOP_N], details_dict if DEV_MODE else None