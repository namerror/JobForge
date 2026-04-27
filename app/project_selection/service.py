from __future__ import annotations

import logging
import time

from app.config import settings
from app.metrics import metrics
from app.project_selection.models import ProjectSelectRequest, ProjectSelectionResult
from app.project_selection.selector import select_projects

logger = logging.getLogger("project_selector")

DEFAULT_PROJECT_SELECTION_METHOD = "llm"
METRICS_SUBSYSTEM = "project_selection"


def _effective_method(requested_method: str, result: ProjectSelectionResult) -> str:
    details = result.details
    if isinstance(details, dict):
        fallback_method = details.get("_fallback_method")
        if isinstance(fallback_method, str) and fallback_method:
            return fallback_method

        llm_meta = details.get("_project_llm")
        if isinstance(llm_meta, dict) and llm_meta.get("fallback") == "baseline":
            return "baseline"

    if result.ranked_projects:
        return result.ranked_projects[0].method

    return requested_method


def _extract_total_tokens(result: ProjectSelectionResult) -> int:
    details = result.details
    if not isinstance(details, dict):
        return 0

    llm_meta = details.get("_project_llm")
    if not isinstance(llm_meta, dict):
        return 0

    try:
        return int(llm_meta.get("total_tokens", 0) or 0)
    except (TypeError, ValueError):
        return 0


def record_project_selection_error(method: str = "invalid") -> None:
    metrics.inc_request(method=method, subsystem=METRICS_SUBSYSTEM)
    metrics.inc_error(subsystem=METRICS_SUBSYSTEM)


def select_projects_service(req: ProjectSelectRequest) -> ProjectSelectionResult:
    method = req.method or DEFAULT_PROJECT_SELECTION_METHOD
    dev_mode = req.dev_mode if req.dev_mode is not None else settings.DEV_MODE

    start = time.perf_counter()
    request_counted = False

    try:
        result = select_projects(
            context=req.context,
            candidates=req.candidates,
            method=method,
            top_n=req.top_n,
            dev_mode=dev_mode,
        )

        latency_ms = (time.perf_counter() - start) * 1000.0
        effective_method = _effective_method(method, result)
        metrics.inc_request(method=effective_method, subsystem=METRICS_SUBSYSTEM)
        request_counted = True
        metrics.observe_tokens(_extract_total_tokens(result), subsystem=METRICS_SUBSYSTEM)
        metrics.observe_latency_ms(latency_ms, subsystem=METRICS_SUBSYSTEM)

        logger.info(
            "select_projects",
            extra={
                "event": "select_projects",
                "job_title": req.context.title,
                "method": effective_method,
                "requested_method": method,
                "top_n": req.top_n,
                "latency_ms": round(latency_ms, 3),
                "candidate_count": len(req.candidates),
                "selected_count": len(result.selected_project_ids),
            },
        )

        return result

    except Exception:
        if not request_counted:
            metrics.inc_request(method=method, subsystem=METRICS_SUBSYSTEM)
        metrics.inc_error(subsystem=METRICS_SUBSYSTEM)
        logger.exception(
            "select_projects_failed",
            extra={"event": "select_projects_failed", "job_title": req.context.title, "method": method},
        )
        raise
