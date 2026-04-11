from __future__ import annotations

import logging
from typing import Any

from app.scoring.baseline import baseline_select_skills, normalize_skill
from app.services.llm_client import LLMClientError, score_skills_with_llm

logger = logging.getLogger("llm_scorer")

CATEGORIES = ("technology", "programming", "concepts")


class LLMValidationError(ValueError):
    """Raised when a model response is too malformed to rank safely."""


def _fallback_to_baseline(
    *,
    job_role: str,
    technology: list[str],
    programming: list[str],
    concepts: list[str],
    job_text: str | None,
    top_n: int | None,
    dev_mode: bool,
    warning: str,
) -> tuple[dict, dict | None]:
    selected, details = baseline_select_skills(
        job_role=job_role,
        technology=technology,
        programming=programming,
        concepts=concepts,
        job_text=job_text,
        top_n=top_n,
        dev_mode=dev_mode,
    )
    if dev_mode:
        details = details or {}
        warnings = details.setdefault("_warnings", [])
        warnings.append(warning)
        details["_llm"] = {"fallback": "baseline", "reason": warning}
    return selected, details if dev_mode else None


def _validate_scores(
    raw_scores: Any,
    category_inputs: dict[str, list[str]],
) -> tuple[dict[str, dict[str, int]], list[str]]:
    if not isinstance(raw_scores, dict):
        raise LLMValidationError("LLM scores must be a JSON object")

    validated: dict[str, dict[str, int]] = {}
    warnings: list[str] = []

    for category in CATEGORIES:
        category_scores = raw_scores.get(category)
        if not isinstance(category_scores, dict):
            raise LLMValidationError(f"LLM scores missing or malformed category: {category}")

        allowed = set(category_inputs[category])
        valid_category: dict[str, int] = {}
        for skill, score in category_scores.items():
            if skill not in allowed:
                warnings.append(f"discarded invented or moved skill '{skill}' in {category}")
                continue
            if not isinstance(score, int) or isinstance(score, bool) or score < 0 or score > 3:
                warnings.append(f"discarded invalid score for '{skill}' in {category}")
                continue
            valid_category[skill] = score

        validated[category] = valid_category

    return validated, warnings


def _rank_category(
    skills: list[str],
    scores: dict[str, int],
    top_n: int | None,
    dev_mode: bool,
) -> tuple[list[str], dict | None]:
    scored = []
    for skill in skills:
        if skill in scores:
            scored.append((skill, scores[skill], normalize_skill(skill)))

    scored.sort(key=lambda item: (-item[1], item[2]))
    ranked = [skill for skill, _, _ in scored[:top_n]]

    details = None
    if dev_mode:
        details = {
            skill: {"score": score, "normalized_skill": normalized}
            for skill, score, normalized in scored
        }
    return ranked, details


def llm_select_skills(
    job_role: str,
    technology: list[str],
    programming: list[str],
    concepts: list[str],
    job_text: str | None = None,
    top_n: int | None = None,
    dev_mode: bool = False,
) -> tuple[dict, dict | None]:
    """Select top skills per category using LLM scoring and local ranking."""
    category_inputs = {
        "technology": technology,
        "programming": programming,
        "concepts": concepts,
    }

    try:
        llm_result = score_skills_with_llm(
            job_role=job_role,
            job_text=job_text,
            technology=technology,
            programming=programming,
            concepts=concepts,
        )
        scores, warnings = _validate_scores(llm_result.scores, category_inputs)
    except (LLMClientError, LLMValidationError) as exc:
        logger.warning(
            "llm_fallback_to_baseline",
            extra={"event": "llm_fallback_to_baseline", "role": job_role, "error": str(exc)},
        )
        return _fallback_to_baseline(
            job_role=job_role,
            technology=technology,
            programming=programming,
            concepts=concepts,
            job_text=job_text,
            top_n=top_n,
            dev_mode=dev_mode,
            warning=f"LLM selection failed; fell back to baseline: {exc}",
        )

    selected: dict[str, list[str]] = {}
    all_details: dict | None = {} if dev_mode else None

    for category, skills in category_inputs.items():
        ranked, details = _rank_category(
            skills=skills,
            scores=scores[category],
            top_n=top_n,
            dev_mode=dev_mode,
        )
        selected[category] = ranked
        if dev_mode and details is not None:
            all_details[category] = details  # type: ignore[index]

    if dev_mode:
        all_details["_llm"] = llm_result.metadata  # type: ignore[index]
        if warnings:
            all_details["_warnings"] = warnings  # type: ignore[index]

    return selected, all_details if dev_mode else None
