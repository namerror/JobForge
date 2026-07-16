from __future__ import annotations

import logging
import time
from typing import Any

from app.config import settings
from app.job_focus_generation.llm_client import (
    JobFocusLLMClientError,
    derive_job_focus_with_llm,
)
from app.job_focus_generation.models import JobFocusRequest, JobFocusResponse
from app.metrics import metrics

logger = logging.getLogger("job_focus_generator")

METRICS_SUBSYSTEM = "job_focus_generation"


class JobFocusGenerationError(RuntimeError):
    """Raised when job-focus generation cannot complete."""


def _extract_total_tokens(result_metadata: dict[str, Any] | None) -> int:
    if not isinstance(result_metadata, dict):
        return 0
    try:
        return int(result_metadata.get("total_tokens", 0) or 0)
    except (TypeError, ValueError):
        return 0


def record_job_focus_generation_error(method: str = "llm") -> None:
    metrics.inc_request(method=method, subsystem=METRICS_SUBSYSTEM)
    metrics.inc_error(subsystem=METRICS_SUBSYSTEM)


def derive_job_focus_service(req: JobFocusRequest) -> JobFocusResponse:
    dev_mode = req.dev_mode if req.dev_mode is not None else settings.DEV_MODE
    start = time.perf_counter()
    request_counted = False
    llm_metadata: dict[str, Any] | None = None

    try:
        llm_result = derive_job_focus_with_llm(
            title=req.title,
            description=req.description,
            model=req.llm_model,
            max_output_tokens=req.llm_max_output_tokens,
        )
        llm_metadata = llm_result.metadata

        latency_ms = (time.perf_counter() - start) * 1000.0
        metrics.inc_request(method="llm", subsystem=METRICS_SUBSYSTEM)
        request_counted = True
        metrics.observe_tokens(_extract_total_tokens(llm_metadata), subsystem=METRICS_SUBSYSTEM)
        metrics.observe_latency_ms(latency_ms, subsystem=METRICS_SUBSYSTEM)

        logger.info(
            "derive_job_focus",
            extra={
                "event": "derive_job_focus",
                "subsystem": METRICS_SUBSYSTEM,
                "job_title": req.title,
                "method": "llm",
                "latency_ms": round(latency_ms, 3),
            },
        )

        details: dict[str, Any] | None = None
        if dev_mode:
            details = {
                "method": "llm",
                "_job_focus_llm": llm_metadata,
            }

        return JobFocusResponse(job_focus=llm_result.job_focus, details=details)

    except JobFocusLLMClientError as exc:
        if not request_counted:
            metrics.inc_request(method="llm", subsystem=METRICS_SUBSYSTEM)
        metrics.inc_error(subsystem=METRICS_SUBSYSTEM)
        logger.warning(
            "derive_job_focus_failed",
            extra={
                "event": "derive_job_focus_failed",
                "subsystem": METRICS_SUBSYSTEM,
                "job_title": req.title,
                "method": "llm",
                "error": str(exc),
            },
        )
        raise JobFocusGenerationError(str(exc)) from exc
