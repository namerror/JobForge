from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from app.config import settings
from app.link_scanning.models import LinkScanHighlight, LinkScanJobContext
from app.skill_selection.llm_client import supports_temperature
from resume_evidence.models import ProjectRecord

logger = logging.getLogger("link_scanning_llm_client")


class LinkScanningLLMClientError(RuntimeError):
    """Raised when a link-scanning request or response cannot be used."""


@dataclass
class LLMLinkScanResult:
    highlights: list[LinkScanHighlight]
    metadata: dict[str, Any]


def build_link_scan_schema() -> dict[str, Any]:
    highlight_schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "minLength": 1},
            "source_url": {"type": "string", "minLength": 1},
        },
        "required": ["text", "source_url"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "highlights": {
                "type": "array",
                "items": highlight_schema,
                "maxItems": 12,
            }
        },
        "required": ["highlights"],
        "additionalProperties": False,
    }


def build_link_scan_prompt_payload(
    *,
    context: LinkScanJobContext,
    project: ProjectRecord,
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
            "links": project.links or [],
        },
        "grounding_rules": [
            "Read every supplied project link using web search.",
            "For each link, use only the single page the URL resolves to after normal redirects.",
            "Collect factual project evidence supported by the linked page.",
            "The job description may guide emphasis but is not evidence of user experience.",
            "Return concise evidence highlights, not polished resume bullets.",
            "Do not add skills or infer technologies beyond what the page directly supports.",
            "Omit unsupported claims instead of guessing.",
        ],
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def build_link_scan_instructions() -> str:
    return (
        "You are a deterministic evidence collector for grounded resume generation. "
        "Use web search to open and read every URL in the supplied project.links list. "
        "For each URL, inspect only the page that URL resolves to after normal redirects; "
        "do not crawl additional pages. Extract concise factual highlights about the project "
        "that are directly supported by those pages and useful for later resume refinement. "
        "The target job may guide which facts are most relevant, but it is not evidence. "
        "Return JSON only. Do not include skills, technologies, metrics, dates, ownership, "
        "affiliations, or outcomes unless the scanned page directly supports them. "
        "Set source_url to the linked or final resolved page URL supporting the highlight. "
        "If the pages do not provide new grounded facts, return an empty highlights array."
    )


def build_link_scan_response_create_kwargs(
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
        "tools": [{"type": "web_search"}],
        "tool_choice": "required",
        "include": ["web_search_call.action.sources"],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "project_link_scan",
                "schema": schema,
                "strict": True,
            }
        },
    }
    if supports_temperature(model):
        kwargs["temperature"] = 0
    return kwargs


def _usage_metadata(response: Any) -> dict[str, int]:
    usage = getattr(response, "usage", None)
    return {
        "prompt_tokens": int(getattr(usage, "input_tokens", 0) or 0),
        "completion_tokens": int(getattr(usage, "output_tokens", 0) or 0),
        "total_tokens": int(getattr(usage, "total_tokens", 0) or 0),
    }


def _extract_source_urls(value: Any) -> list[str]:
    urls: list[str] = []

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            raw_url = item.get("url")
            if isinstance(raw_url, str) and raw_url.strip():
                urls.append(raw_url.strip())
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)
        else:
            for attr in ("url",):
                raw_url = getattr(item, attr, None)
                if isinstance(raw_url, str) and raw_url.strip():
                    urls.append(raw_url.strip())
            output = getattr(item, "output", None)
            if output is not None:
                visit(output)
            action = getattr(item, "action", None)
            if action is not None:
                visit(action)
            sources = getattr(item, "sources", None)
            if sources is not None:
                visit(sources)

    visit(getattr(value, "output", None))
    return list(dict.fromkeys(urls))


def _validate_link_scan_response(
    raw_response: Any,
    *,
    allowed_source_urls: list[str],
) -> list[LinkScanHighlight]:
    if not isinstance(raw_response, dict):
        raise LinkScanningLLMClientError("Link-scanning LLM response must be a JSON object")

    raw_highlights = raw_response.get("highlights")
    if not isinstance(raw_highlights, list):
        raise LinkScanningLLMClientError("Link-scanning LLM response must include highlights")

    allowed_sources = set(allowed_source_urls)
    highlights: list[LinkScanHighlight] = []
    seen: set[tuple[str, str]] = set()
    for index, raw_highlight in enumerate(raw_highlights, start=1):
        if not isinstance(raw_highlight, dict):
            raise LinkScanningLLMClientError(f"Highlight {index} must be an object")

        try:
            highlight = LinkScanHighlight.model_validate(raw_highlight)
        except Exception as exc:
            raise LinkScanningLLMClientError(f"Highlight {index} was invalid: {exc}") from exc

        if allowed_sources and highlight.source_url not in allowed_sources:
            raise LinkScanningLLMClientError(
                f"Highlight {index} source_url was not one of the scanned or cited URLs"
            )

        key = (highlight.text.casefold(), highlight.source_url)
        if key in seen:
            continue
        seen.add(key)
        highlights.append(highlight)

    return highlights


def scan_project_links_with_llm(
    *,
    context: LinkScanJobContext,
    project: ProjectRecord,
    model: str | None = None,
    max_output_tokens: int | None = None,
) -> LLMLinkScanResult:
    links = project.links or []
    if not links:
        return LLMLinkScanResult(
            highlights=[],
            metadata={
                "model": model if model is not None else settings.LINK_SCANNING_LLM_MODEL,
                "api_calls": 0,
                "scanned_links": [],
                "source_urls": [],
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "latency_ms": 0.0,
            },
        )

    api_key = getattr(settings, "OPENAI_API_KEY", "")
    if not api_key.strip():
        raise LinkScanningLLMClientError("OPENAI_API_KEY is required for link scanning")

    effective_model = model if model is not None else settings.LINK_SCANNING_LLM_MODEL
    effective_max_output_tokens = (
        max_output_tokens
        if max_output_tokens is not None
        else settings.LINK_SCANNING_LLM_MAX_OUTPUT_TOKENS
    )

    prompt_payload = build_link_scan_prompt_payload(context=context, project=project)
    schema = build_link_scan_schema()
    instructions = build_link_scan_instructions()

    start = time.perf_counter()
    try:
        client = OpenAI(api_key=api_key)
        create_kwargs = build_link_scan_response_create_kwargs(
            model=effective_model,
            instructions=instructions,
            prompt_payload=prompt_payload,
            schema=schema,
            max_output_tokens=effective_max_output_tokens,
        )
        response = client.responses.create(**create_kwargs)
    except Exception as exc:
        logger.exception(
            "link_scanning_llm_request_failed",
            extra={
                "event": "link_scanning_llm_request_failed",
                "subsystem": "link_scanning",
                "model": effective_model,
                "project_id": project.id,
            },
        )
        raise LinkScanningLLMClientError(f"Link-scanning LLM request failed: {exc}") from exc

    latency_ms = (time.perf_counter() - start) * 1000.0
    output_text = getattr(response, "output_text", None)
    if not output_text:
        raise LinkScanningLLMClientError("Link-scanning LLM response did not include output_text")

    try:
        raw_response = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise LinkScanningLLMClientError(
            f"Link-scanning LLM response was not valid JSON: {exc}"
        ) from exc

    source_urls = _extract_source_urls(response)
    allowed_source_urls = list(dict.fromkeys([*links, *source_urls]))
    highlights = _validate_link_scan_response(
        raw_response,
        allowed_source_urls=allowed_source_urls,
    )
    metadata = {
        "model": effective_model,
        "api_calls": 1,
        "latency_ms": round(latency_ms, 3),
        "scanned_links": links,
        "source_urls": source_urls,
        **_usage_metadata(response),
    }
    return LLMLinkScanResult(highlights=highlights, metadata=metadata)
