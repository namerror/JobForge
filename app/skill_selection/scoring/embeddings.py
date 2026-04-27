import logging

import numpy as np
import openai

from app.skill_selection.scoring.synonyms import SYNONYM_TO_NORMALIZED
from app.skill_selection.embedding_client import embed_role, embed_skills
from app.skill_selection.embedding_cache import EmbeddingCache
from app.config import settings

cache = EmbeddingCache(settings.EMBEDDING_MODEL)

logger = logging.getLogger("embeddings_scorer")

MIN_ROLE_TEXT_CHARS = 8

    
def normalize_skill(skill: str) -> str:
    """Normalize skill names to a standard format."""
    s = skill.strip().lower()
    return SYNONYM_TO_NORMALIZED.get(s, s)


def construct_role_text(job_role: str, job_text: str | None) -> str:
    """Construct a text representation of the role by combining the job role and job description."""
    normalized_role = job_role.strip().lower()
    if job_text:
        return f"{normalized_role}\n{job_text.strip()}"
    return normalized_role


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a_arr = np.array(a, dtype=np.float64)
    b_arr = np.array(b, dtype=np.float64)
    norm = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    if norm == 0.0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / norm)


def embedding_rank_skills(
    skills: list[str],
    role_vec: list[float],
    top_n: int | None = None,
    dev_mode: bool = False,
) -> tuple[list[str], dict | None]:
    """Rank skills by cosine similarity to the role embedding.

    Returns (ranked_skills, details_dict | None).
    """
    if not skills:
        return [], {} if dev_mode else None

    normalized_skills = [normalize_skill(s) for s in skills]

    skill_vecs: list[list[float] | None] = [None] * len(normalized_skills)
    missing_texts: list[str] = []
    missing_indices: list[int] = []

    for idx, normalized in enumerate(normalized_skills):
        cached = cache.cache_lookup(normalized, type="skill")
        if cached is None:
            missing_texts.append(normalized)
            missing_indices.append(idx)
        else:
            skill_vecs[idx] = cached

    if missing_texts:
        missing_vecs = embed_skills(missing_texts)
        if len(missing_texts) != len(missing_vecs):
            logger.error(
                "embedding_length_mismatch",
                extra={
                    "event": "embedding_length_mismatch",
                    "num_skills": len(missing_texts),
                    "num_skill_vecs": len(missing_vecs),
                },
            )
            raise ValueError("Number of skill embeddings does not match number of skills")

        for normalized, idx, vec in zip(missing_texts, missing_indices, missing_vecs):
            skill_vecs[idx] = vec
            cache.cache_store(normalized, vec, type="skill")

    scored = []

    # check lengths match
    if len(normalized_skills) != len(skill_vecs) or any(vec is None for vec in skill_vecs):
        logger.error(
            "embedding_length_mismatch",
            extra={
                "event": "embedding_length_mismatch",
                "num_skills": len(normalized_skills),
                "num_skill_vecs": len(skill_vecs),
            },
        )
        raise ValueError("Number of skill embeddings does not match number of skills")

    for skill, normalized, vec in zip(skills, normalized_skills, skill_vecs):
        sim = cosine_similarity(role_vec, vec)
        scored.append((skill, sim, normalized))

    # Sort: similarity desc, then normalized name asc (stable tie-break)
    scored.sort(key=lambda x: (-x[1], x[2]))

    ranked = [skill for skill, _, _ in scored[:top_n]]

    details = None
    if dev_mode:
        details = {
            skill: {"similarity": round(sim, 6), "normalized_skill": norm}
            for skill, sim, norm in scored
        }

    return ranked, details


def embedding_select_skills(
    job_role: str,
    technology: list[str],
    programming: list[str],
    concepts: list[str],
    job_text: str | None = None,
    top_n: int | None = None,
    dev_mode: bool = False,
) -> tuple[dict, dict | None]:
    """Select top skills per category using embedding similarity.

    Mirrors the baseline_select_skills() interface.
    """
    role_text = construct_role_text(job_role, job_text)

    warnings: list[str] = []
    if len(role_text) < MIN_ROLE_TEXT_CHARS:
        msg = f"role text is very short ({len(role_text)} chars); embeddings may be low quality"
        warnings.append(msg)
        logger.warning(
            "role_text_too_short",
            extra={"event": "role_text_too_short", "role": job_role, "length": len(role_text)},
        )

    selected_skills: dict[str, list[str]] = {}
    all_details: dict | None = {} if dev_mode else None

    category_inputs = {
        "technology": technology,
        "programming": programming,
        "concepts": concepts,
    }

    try:
        
        role_vec = cache.cache_lookup(role_text, type='role')
        if role_vec is None:
            role_vec = embed_role(role_text)
            cache.cache_store(role_text, role_vec, type='role')

        for category, category_skills in category_inputs.items():
            ranked, details = embedding_rank_skills(
                skills=category_skills,
                role_vec=role_vec,
                top_n=top_n,
                dev_mode=dev_mode,
            )
            selected_skills[category] = ranked
            if dev_mode and details is not None:
                all_details[category] = details  # type: ignore[index]

    except openai.RateLimitError as e:
        logger.error(
            "embedding_rate_limit",
            extra={"event": "embedding_rate_limit", "role": job_role, "error": str(e)},
        )
        raise RuntimeError(f"Embedding API rate limit reached: {e}") from e

    if dev_mode and warnings:
        all_details["_warnings"] = warnings  # type: ignore[index]

    return selected_skills, all_details if dev_mode else None
