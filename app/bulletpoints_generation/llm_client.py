from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from app.bulletpoints_generation.models import BulletCountRange, BulletJobContext
from app.config import settings
from app.skill_selection.llm_client import supports_temperature
from resume_evidence.models import ProjectRecord

logger = logging.getLogger("bulletpoints_llm_client")


class BulletPointLLMClientError(RuntimeError):
    """Raised when a bullet-point generation request or response cannot be used."""


@dataclass
class LLMBulletPointResult:
    bullet_points: list[str]
    metadata: dict[str, Any]


def build_bulletpoint_schema(count_range: BulletCountRange) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "bullet_points": {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
                "minItems": count_range.min,
                "maxItems": count_range.max,
            }
        },
        "required": ["bullet_points"],
        "additionalProperties": False,
    }


def build_bulletpoint_prompt_payload(
    *,
    context: BulletJobContext,
    project: ProjectRecord,
    count_range: BulletCountRange,
) -> str:
    payload = {
        "job": {
            "title": context.title,
            "description": context.description or "",
        },
        "project": {
            "id": project.id,
            "name": project.name,
            "summary": project.summary,
            "highlights": project.highlights,
            "active": project.active,
            "skills": project.skills.model_dump(),
        },
        "bullet_count_range": count_range.model_dump(),
        "grounding_rules": [
            "Use only the supplied project evidence as the source of user experience.",
            "The job description may guide emphasis but is not evidence of user experience.",
            "Omit unsupported claims instead of guessing.",
            "Return plain bullet text without leading bullet symbols.",
        ],
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def build_bulletpoint_instructions(count_range: BulletCountRange) -> str:
    count_instruction = (
        f"Return exactly {count_range.min} bullet point strings."
        if count_range.min == count_range.max
        else (
            f"Return between {count_range.min} and {count_range.max} bullet point strings, "
            "choosing the count that best represents the supplied evidence."
        )
    )
    return (
        "You are a deterministic resume bullet writer. Return JSON only. "
        f"{count_instruction} Tailor the project evidence to the target job while staying "
        "grounded in the supplied project summary, highlights, and skills. Maximize the user's chances of getting an interview by creating strong, ATS-friendly resume bullets. "
        "Use strong action verbs + task + impact (prioritize measurable results) and follow best practices for resume bullet writing. "
        "Some appropriate amount of larping to decorate the bullet points is fine, but do not fabricate any details that are not supported by the supplied evidence. "
        "Each string must be a polished resume bullet without a leading bullet marker."
    )


def _usage_metadata(response: Any) -> dict[str, int]:
    usage = getattr(response, "usage", None)
    return {
        "prompt_tokens": int(getattr(usage, "input_tokens", 0) or 0),
        "completion_tokens": int(getattr(usage, "output_tokens", 0) or 0),
        "total_tokens": int(getattr(usage, "total_tokens", 0) or 0),
    }


def build_bulletpoint_response_create_kwargs(
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
                "name": "project_bullet_points",
                "schema": schema,
                "strict": True,
            }
        },
    }
    if supports_temperature(model):
        kwargs["temperature"] = 0
    return kwargs


def _validate_bullet_points(raw_response: Any, count_range: BulletCountRange) -> list[str]:
    if not isinstance(raw_response, dict):
        raise BulletPointLLMClientError("Bullet-point LLM response must be a JSON object")

    raw_bullets = raw_response.get("bullet_points")
    if not isinstance(raw_bullets, list):
        raise BulletPointLLMClientError("Bullet-point LLM response must include bullet_points")

    bullets: list[str] = []
    for index, bullet in enumerate(raw_bullets, start=1):
        if not isinstance(bullet, str):
            raise BulletPointLLMClientError(f"Bullet point {index} must be a string")
        normalized = bullet.strip()
        if not normalized:
            raise BulletPointLLMClientError(f"Bullet point {index} must not be empty")
        cleaned = normalized.lstrip("-* ").strip()
        if not cleaned:
            raise BulletPointLLMClientError(f"Bullet point {index} must not be empty")
        bullets.append(cleaned)

    if len(bullets) < count_range.min or len(bullets) > count_range.max:
        raise BulletPointLLMClientError(
            "Bullet-point LLM response count was outside the requested range"
        )

    return bullets


def generate_bulletpoints_with_llm(
    *,
    context: BulletJobContext,
    project: ProjectRecord,
    count_range: BulletCountRange,
    model: str | None = None,
    max_output_tokens: int | None = None,
) -> LLMBulletPointResult:
    prompt_payload = build_bulletpoint_prompt_payload(
        context=context,
        project=project,
        count_range=count_range,
    )
    schema = build_bulletpoint_schema(count_range)
    instructions = build_bulletpoint_instructions(count_range)

    api_key = getattr(settings, "OPENAI_API_KEY", "")
    if not api_key.strip():
        raise BulletPointLLMClientError("OPENAI_API_KEY is required for bullet-point generation")

    effective_model = model if model is not None else settings.BULLETPOINTS_LLM_MODEL
    effective_max_output_tokens = (
        max_output_tokens
        if max_output_tokens is not None
        else settings.BULLETPOINTS_LLM_MAX_OUTPUT_TOKENS
    )

    start = time.perf_counter()
    try:
        client = OpenAI(api_key=api_key)
        create_kwargs = build_bulletpoint_response_create_kwargs(
            model=effective_model,
            instructions=instructions,
            prompt_payload=prompt_payload,
            schema=schema,
            max_output_tokens=effective_max_output_tokens,
        )
        response = client.responses.create(**create_kwargs)
    except Exception as exc:
        logger.exception(
            "bulletpoints_llm_request_failed",
            extra={
                "event": "bulletpoints_llm_request_failed",
                "subsystem": "bulletpoints_generation",
                "model": effective_model,
            },
        )
        raise BulletPointLLMClientError(f"Bullet-point LLM request failed: {exc}") from exc

    latency_ms = (time.perf_counter() - start) * 1000.0
    output_text = getattr(response, "output_text", None)
    if not output_text:
        raise BulletPointLLMClientError("Bullet-point LLM response did not include output_text")

    try:
        raw_response = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise BulletPointLLMClientError(
            f"Bullet-point LLM response was not valid JSON: {exc}"
        ) from exc

    bullets = _validate_bullet_points(raw_response, count_range)
    metadata = {
        "model": effective_model,
        "api_calls": 1,
        "latency_ms": round(latency_ms, 3),
        **_usage_metadata(response),
    }
    return LLMBulletPointResult(bullet_points=bullets, metadata=metadata)
