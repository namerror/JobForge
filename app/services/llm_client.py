from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from app.config import settings

logger = logging.getLogger("llm_client")

CATEGORIES = ("technology", "programming", "concepts")


class LLMClientError(RuntimeError):
    """Raised when the LLM request or response cannot be used."""


@dataclass
class LLMScoreResult:
    scores: dict[str, dict[str, Any]]
    metadata: dict[str, Any]


def build_score_schema(category_inputs: dict[str, list[str]]) -> dict[str, Any]:
    """Build a strict JSON schema for the exact candidate skill names."""
    properties: dict[str, Any] = {}
    for category in CATEGORIES:
        unique_skills = list(dict.fromkeys(category_inputs.get(category, [])))
        properties[category] = {
            "type": "object",
            "properties": {
                skill: {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 3,
                    "description": "0=not relevant, 1=weak, 2=good, 3=strong",
                }
                for skill in unique_skills
            },
            "required": unique_skills,
            "additionalProperties": False,
        }

    return {
        "type": "object",
        "properties": properties,
        "required": list(CATEGORIES),
        "additionalProperties": False,
    }


def build_prompt_payload(
    *,
    job_role: str,
    job_text: str | None,
    technology: list[str],
    programming: list[str],
    concepts: list[str],
) -> str:
    """Serialize the scorer input as compact JSON for the fixed prompt."""
    payload = {
        "job_role": job_role,
        "job_text": job_text or "",
        "skills": {
            "technology": technology,
            "programming": programming,
            "concepts": concepts,
        },
        "score_scale": {
            "0": "not relevant",
            "1": "weak relevance",
            "2": "good relevance",
            "3": "strong relevance",
        },
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _usage_metadata(response: Any) -> dict[str, int]:
    usage = getattr(response, "usage", None)
    return {
        "prompt_tokens": int(getattr(usage, "input_tokens", 0) or 0),
        "completion_tokens": int(getattr(usage, "output_tokens", 0) or 0),
        "total_tokens": int(getattr(usage, "total_tokens", 0) or 0),
    }


def score_skills_with_llm(
    *,
    job_role: str,
    job_text: str | None,
    technology: list[str],
    programming: list[str],
    concepts: list[str],
) -> LLMScoreResult:
    """Score every candidate skill through the OpenAI Responses API."""
    category_inputs = {
        "technology": technology,
        "programming": programming,
        "concepts": concepts,
    }
    prompt_payload = build_prompt_payload(
        job_role=job_role,
        job_text=job_text,
        technology=technology,
        programming=programming,
        concepts=concepts,
    )
    schema = build_score_schema(category_inputs)

    instructions = (
        "You are a deterministic skill relevance scorer. "
        "Return JSON only. Score every provided candidate skill for the given job role "
        "and optional job text. Do not add, remove, rename, or move skills between "
        "categories. Scores must be integers from 0 to 3."
    )

    api_key = getattr(settings, "OPENAI_API_KEY", "")
    if not api_key.strip():
        raise LLMClientError("OPENAI_API_KEY is required for LLM scoring")

    start = time.perf_counter()
    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=settings.LLM_MODEL,
            instructions=instructions,
            input=prompt_payload,
            temperature=0,
            max_output_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
            tools=[],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "skill_scores",
                    "schema": schema,
                    "strict": True,
                }
            },
        )
    except Exception as exc:
        logger.exception(
            "llm_request_failed",
            extra={"event": "llm_request_failed", "model": settings.LLM_MODEL},
        )
        raise LLMClientError(f"LLM request failed: {exc}") from exc

    latency_ms = (time.perf_counter() - start) * 1000.0
    output_text = getattr(response, "output_text", None)
    if not output_text:
        raise LLMClientError("LLM response did not include output_text")

    try:
        scores = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise LLMClientError(f"LLM response was not valid JSON: {exc}") from exc

    metadata = {
        "model": settings.LLM_MODEL,
        "api_calls": 1,
        "latency_ms": round(latency_ms, 3),
        **_usage_metadata(response),
    }
    return LLMScoreResult(scores=scores, metadata=metadata)
