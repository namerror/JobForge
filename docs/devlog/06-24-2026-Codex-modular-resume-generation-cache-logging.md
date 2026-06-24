### 2026-06-24 - Modular Resume Generation Cache Logging

**Agent:** Codex (GPT-5)

**Changes:**
- `resume_generation/models.py:189-212` - Split shared bullet generation config into project and experience sections, and reject the legacy shared key.
- `resume_generation/bullet_points.py:18-91` - Routed project and experience bullet payloads through their own config sections and cache stages.
- `resume_generation/cache.py:19-99` - Added source-aware cache result metadata while preserving the existing dict-returning cache API.
- `resume_generation/selection.py:103-152` - Logged cache response source, cache status, endpoint, namespace, and cache key for orchestration HTTP stages.
- `resume_generation/main.py:58-227` - Added INFO logs for pipeline start, stage start/complete/skip, artifact write, and pipeline completion.
- `app/main.py:88-121` - Added route-entry INFO logs for content-generation HTTP endpoints.
- `tests/test_resume_generation.py` - Added config split, cache invalidation, cache source logging, pipeline logging, and route logging tests.
- `docs/decisions/011-modular-bullet-generation-cache-config.md` - Recorded the config split decision.

**Rationale:**
Project and experience bullet generation used to share one config section, so changing the model or token budget for one section changed both request payload families and invalidated both cache groups. Splitting the config keeps cache keys aligned with the actual stage input. Source-aware logging was added at the orchestration HTTP wrapper because app routes cannot observe cache hits that bypass HTTP.

**Tests:**
- `test_experience_bullet_model_change_does_not_regenerate_project_bullets`: validates experience model changes only rerun experience bullet generation.
- `test_project_bullet_model_change_does_not_regenerate_experience_bullets`: validates project model changes only rerun project bullet generation.
- `test_skill_evidence_change_only_invalidates_skill_selection`: validates global skill edits do not invalidate project selection or bullet generation.
- `test_cached_project_bullet_generation_logs_response_source`: validates cache miss/hit source logging.
- `test_resume_generation_pipeline_logs_stage_events`: validates pipeline stage logging.
- `test_generate_bulletpoints_route_logs_http_source`: validates app route-entry logging for HTTP-sourced content generation.

**Impact:**
Resume generation cache reuse is now modular across project and experience bullet generation, and pipeline logs identify whether each generated response came from cache or HTTP.
