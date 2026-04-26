from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from app.config import settings
from app.project_selection.models import ProjectCandidate, ProjectJobContext
from app.services.llm_client import supports_temperature

logger = logging.getLogger("project_llm_client")


class ProjectLLMClientError(RuntimeError):
    """Raised when a project LLM request or response cannot be used."""


@dataclass
class LLMProjectScoreResult:
    scores: dict[str, Any]
    metadata: dict[str, Any]


def build_project_score_schema(project_ids: list[str]) -> dict[str, Any]:
    unique_ids = list(dict.fromkeys(project_ids))
    return {
        "type": "object",
        "properties": {
            project_id: {
                "type": "integer",
                "minimum": 0,
                "maximum": 3,
                "description": "0=not relevant, 1=weak, 2=good, 3=strong",
            }
            for project_id in unique_ids
        },
        "required": unique_ids,
        "additionalProperties": False,
    }


def build_project_prompt_payload(
    *,
    context: ProjectJobContext,
    candidates: list[ProjectCandidate],
) -> str:
    payload = {
        "job": {
            "title": context.title,
            "description": context.description or "",
        },
        "projects": [
            {
                "id": candidate.id,
                "name": candidate.name,
                "summary": candidate.summary,
                "skills": candidate.skills.model_dump(),
            }
            for candidate in candidates
        ],
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


def build_project_response_create_kwargs(
    *,
    model: str,
    instructions: str,
    prompt_payload: str,
    schema: dict[str, Any],
    max_output_tokens: int,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "model": model,
        "instructions": instructions,
        "input": prompt_payload,
        "max_output_tokens": max_output_tokens,
        "tools": [],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "project_scores",
                "schema": schema,
                "strict": True,
            }
        },
    }
    if supports_temperature(model):
        kwargs["temperature"] = 0
    return kwargs


def score_projects_with_llm(
    *,
    context: ProjectJobContext,
    candidates: list[ProjectCandidate],
) -> LLMProjectScoreResult:
    prompt_payload = build_project_prompt_payload(context=context, candidates=candidates)
    schema = build_project_score_schema([candidate.id for candidate in candidates])
    instructions = (
        "You are a deterministic project relevance scorer. Return JSON only. "
        "Score every provided candidate project for the given job context using only "
        "the project summary and categorized skills. Do not add, remove, rename, or "
        "rewrite projects. Scores must be integers from 0 to 3."
    )

    api_key = getattr(settings, "OPENAI_API_KEY", "")
    if not api_key.strip():
        raise ProjectLLMClientError("OPENAI_API_KEY is required for project LLM scoring")

    start = time.perf_counter()
    try:
        client = OpenAI(api_key=api_key)
        create_kwargs = build_project_response_create_kwargs(
            model=settings.LLM_MODEL,
            instructions=instructions,
            prompt_payload=prompt_payload,
            schema=schema,
            max_output_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
        )
        response = client.responses.create(**create_kwargs)
    except Exception as exc:
        logger.exception(
            "project_llm_request_failed",
            extra={"event": "project_llm_request_failed", "model": settings.LLM_MODEL},
        )
        raise ProjectLLMClientError(f"Project LLM request failed: {exc}") from exc

    latency_ms = (time.perf_counter() - start) * 1000.0
    output_text = getattr(response, "output_text", None)
    if not output_text:
        raise ProjectLLMClientError("Project LLM response did not include output_text")

    try:
        scores = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise ProjectLLMClientError(f"Project LLM response was not valid JSON: {exc}") from exc

    metadata = {
        "model": settings.LLM_MODEL,
        "api_calls": 1,
        "latency_ms": round(latency_ms, 3),
        **_usage_metadata(response),
    }
    return LLMProjectScoreResult(scores=scores, metadata=metadata)
