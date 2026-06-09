from __future__ import annotations

import logging
import time
from typing import Any

from app.config import settings
from app.link_scanning.llm_client import (
    LinkScanningLLMClientError,
    scan_project_links_with_llm,
)
from app.link_scanning.models import LinkScanRequest, LinkScanResponse

logger = logging.getLogger("link_scanning")


class LinkScanningError(RuntimeError):
    """Raised when link scanning cannot complete."""


def _extract_total_tokens(result_metadata: dict[str, Any] | None) -> int:
    if not isinstance(result_metadata, dict):
        return 0
    try:
        return int(result_metadata.get("total_tokens", 0) or 0)
    except (TypeError, ValueError):
        return 0


def scan_project_links_service(req: LinkScanRequest) -> LinkScanResponse:
    dev_mode = req.dev_mode if req.dev_mode is not None else settings.DEV_MODE
    start = time.perf_counter()

    try:
        llm_result = scan_project_links_with_llm(
            context=req.context,
            project=req.project,
            model=req.llm_model,
            max_output_tokens=req.llm_max_output_tokens,
        )
    except LinkScanningLLMClientError as exc:
        logger.warning(
            "scan_project_links_failed",
            extra={
                "event": "scan_project_links_failed",
                "subsystem": "link_scanning",
                "project_id": req.project.id,
                "method": "llm",
                "error": str(exc),
            },
        )
        raise LinkScanningError(str(exc)) from exc

    latency_ms = (time.perf_counter() - start) * 1000.0
    logger.info(
        "scan_project_links",
        extra={
            "event": "scan_project_links",
            "subsystem": "link_scanning",
            "project_id": req.project.id,
            "method": "llm",
            "latency_ms": round(latency_ms, 3),
            "highlight_count": len(llm_result.highlights),
            "total_tokens": _extract_total_tokens(llm_result.metadata),
        },
    )

    details = None
    if dev_mode:
        details = {
            "method": "llm",
            "scanned_links": list(req.project.links or []),
            "_link_scanning_llm": llm_result.metadata,
        }

    return LinkScanResponse(
        project_id=req.project.id,
        added_highlights=llm_result.highlights,
        details=details,
    )
