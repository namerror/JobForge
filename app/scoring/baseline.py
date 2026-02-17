import dotenv
import os
from app.scoring.synonyms import SYNONYM_TO_NORMALIZED
from app.scoring.role_profiles import detect_role_family

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

    return score, {"normalized_skill": normalized_skill, "matched_keywords": list(keywords)}

def rank_skills(skills: list[str], role_family: str, category: str, job_text: str | None=None, top_n: int | None=None, include_zero: bool=False) -> tuple[list[str], dict | None]:
    """Rank skills based on their scores."""
    scored_skills = []
    for skill in skills:
        score, details = score_skill(skill, role_family, category, job_text)
        if include_zero or score > 0:
            scored_skills.append((skill, score, details))

    # Sort by score (descending) and then alphabetically
    scored_skills.sort(key=lambda x: (-x[1], x[0]))

    ranked_skills = [skill for skill, score, details in scored_skills]
    details_dict = {skill: {"score": score, **details} for skill, score, details in scored_skills}

    return ranked_skills[:top_n], details_dict

def baseline_select_skills(
    job_role: str,
    technology: list[str],
    programming: list[str],
    concepts: list[str],
    job_text: str | None = None,
    top_n: int | None = None,
    dev_mode: bool = False,
    include_zero: bool = False # whether to include skills with zero score (irrelevant skills) in the output
) -> tuple[dict, dict | None]:
    """Select top skills for a given role family and category."""
    role_family = detect_role_family(job_role)
    selected_skills = {}
    details = {}

    category_inputs = {
        "technology": technology,
        "programming": programming,
        "concepts": concepts,
    }

    for category, category_skills in category_inputs.items():
        ranked_skills, category_details = rank_skills(category_skills, role_family, category, job_text=job_text, top_n=top_n, include_zero=include_zero)
        selected_skills[category] = ranked_skills
        if dev_mode:
            details[category] = category_details

    return selected_skills, details if dev_mode else None