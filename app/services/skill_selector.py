# app/services/skill_selector.py
from __future__ import annotations
import logging
import time
from typing import Any, Dict

from app.config import settings
from app.metrics import metrics
from app.models import SkillSelectRequest, SkillSelectResponse
from app.scoring.baseline import baseline_select_skills

logger = logging.getLogger("skill_selector")

def select_skills_service(req: SkillSelectRequest) -> SkillSelectResponse:
    method = req.method.lower() if req.method is not None else settings.METHOD.lower()
    top_n = req.top_n if req.top_n is not None else settings.TOP_N
    dev_mode = req.dev_mode if req.dev_mode is not None else settings.DEV_MODE  

    start = time.perf_counter()
    metrics.inc_request(method=method)

    try:
        if method != "baseline":
            # We’ll add embeddings/hybrid later, but fail clearly for now
            raise ValueError(f"Unsupported METHOD: {method}")

        selected, meta = baseline_select_skills(
            job_role=req.job_role,
            job_text=req.job_text,
            technology=req.technology,
            programming=req.programming,
            concepts=req.concepts,
            top_n=top_n,
            dev_mode=dev_mode,
        )

        latency_ms = (time.perf_counter() - start) * 1000.0
        metrics.observe_latency_ms(latency_ms)

        logger.info(
            "select_skills",
            extra={
                "event": "select_skills",
                "role": req.job_role,
                "method": method,
                "top_n": top_n,
                "latency_ms": round(latency_ms, 3),
                "category_counts": {k: len(v) for k, v in selected.items()},
            },
        )

        return SkillSelectResponse(
            technology=selected.get("technology", []),
            programming=selected.get("programming", []),
            concepts=selected.get("concepts", []),
            details=meta if dev_mode else None,
        )

    except Exception:
        metrics.inc_error()
        logger.exception(
            "select_skills_failed",
            extra={"event": "select_skills_failed", "role": req.job_role, "method": method},
        )
        raise
