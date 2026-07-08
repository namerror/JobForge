### 2026-07-08 - Resume Generation Token Monitoring

**Agent:** Codex (GPT-5)

**Changes:**
- `resume_generation/token_usage.py:24-133` - Added token usage extraction, per-stage accumulation, and pipeline summary helpers for resume-generation orchestration.
- `resume_generation/selection.py:107-165` - Added response-level token usage extraction to cached and uncached stage HTTP calls, including cache source metadata.
- `resume_generation/main.py:37-263` - Added per-stage token totals to stage completion/skipped logs and emitted a final `resume_generation_token_usage_summary` event.
- `resume_generation/bullet_points.py:19-106` and `resume_generation/link_scanning.py:18-62` - Threaded the optional token monitor through project bullets, experience bullets, and link scanning.
- `tests/test_resume_generation.py:735-900` and `tests/test_resume_generation.py:1825-1900` - Added coverage for token metadata extraction, cached response token logging, stage completion totals, and final summary totals.

**Rationale:**
Resume generation already calls app microservice endpoints that can return LLM usage metadata in `details`, but the orchestration layer only logged stage boundaries and cache source. Tracking usage in the shared cached HTTP wrapper keeps monitoring consistent across selection, link scanning, and bullet-generation stages while preserving existing response schemas and cache behavior.

**Tests:**
- `test_extract_response_token_usage_reads_stage_metadata`: validates supported response metadata keys and defensive coercion.
- `test_cached_project_bullet_generation_logs_response_source`: validates token fields on HTTP and cached response logs.
- `test_resume_generation_pipeline_logs_token_usage_summary`: validates per-stage and pipeline aggregate token totals.
- `PYTHONPATH=. pytest tests/test_resume_generation.py`: validates the resume-generation test suite.

**Impact:**
Pipeline runs now expose structured per-stage token usage for cost and latency monitoring, including cached response context, without changing the generated resume artifact or app API contracts.
