import dotenv
import os
import re
from app.scoring.synonyms import SYNONYM_TO_NORMALIZED
from app.scoring.role_profiles import detect_role_family

TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:#|\+\+)?")


def normalize_skill(skill: str) -> str:
    """Normalize skill names to a standard format."""
    s = skill.strip().lower()
    
    return SYNONYM_TO_NORMALIZED.get(s, s)


def _phrase_tokens(text: str) -> tuple[str, ...]:
    """Tokenize a normalized phrase while expanding known token aliases."""
    tokens: list[str] = []
    for token in TOKEN_PATTERN.findall(text):
        normalized_token = SYNONYM_TO_NORMALIZED.get(token, token)
        tokens.extend(TOKEN_PATTERN.findall(normalized_token) or [normalized_token])

    return tuple(tokens)


def _contains_token_phrase(container: str, phrase: str) -> bool:
    """Return True when phrase appears in container as contiguous full tokens."""
    container_tokens = _phrase_tokens(container)
    phrase_tokens = _phrase_tokens(phrase)

    if not container_tokens or not phrase_tokens or len(phrase_tokens) > len(container_tokens):
        return False

    phrase_length = len(phrase_tokens)
    return any(
        container_tokens[index:index + phrase_length] == phrase_tokens
        for index in range(len(container_tokens) - phrase_length + 1)
    )


def _has_token_boundary_containment(left: str, right: str) -> bool:
    """Check whether either phrase fully contains the other on token boundaries."""
    return _contains_token_phrase(left, right) or _contains_token_phrase(right, left)


def _normalized_profile_keywords(role_family: str, category: str) -> set[str]:
    """Load role profile keywords for a category and canonicalize aliases."""
    from app.scoring.role_profiles import ROLE_PROFILES

    role_profile = ROLE_PROFILES.get(role_family, ROLE_PROFILES["general"])
    keywords = set(role_profile.get(category, {}).get("keywords", []))

    for parent_role in role_profile.get("inherits", []):
        parent_keywords = set(ROLE_PROFILES.get(parent_role, {}).get(category, {}).get("keywords", []))
        keywords.update(parent_keywords)

    return {normalize_skill(keyword) for keyword in keywords}


def score_skill(skill: str, role_family: str, category: str, job_text: str | None=None) -> tuple[float, dict | None]:
    """Score a skill based on its presence in the job text and its relevance to the role profile."""
    normalized_skill = normalize_skill(skill)
    keywords = _normalized_profile_keywords(role_family, category)

    # Exact or token-boundary containment = 3 points, weaker partial match = 1 point
    score = 0.0
    matched_keywords: list[str] = []
    # Handle empty strings - they shouldn't match anything
    if normalized_skill:
        matched_keywords = sorted(
            keyword for keyword in keywords
            if keyword == normalized_skill or _has_token_boundary_containment(normalized_skill, keyword)
        )

    if matched_keywords:
        score = 3.0
    elif normalized_skill:
        matched_keywords = sorted(keyword for keyword in keywords if normalized_skill in keyword)
        if matched_keywords:
            score = 1.0

    return score, {"normalized_skill": normalized_skill, "matched_keywords": matched_keywords}

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
