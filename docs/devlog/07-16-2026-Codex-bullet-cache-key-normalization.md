### 2026-07-16 - Bullet cache key normalization

**Agent:** Codex (GPT-5)

**Changes:**
- `resume_generation/cache.py:54-104` - Added `should_use_cached` so callers can reject incompatible cache hits and refresh the same semantic entry.
- `resume_generation/selection.py:239-290` - Passed cached-entry compatibility checks through the shared `_cached_post_json` wrapper.
- `resume_generation/bullet_points.py:20-79` - Added bullet count compatibility, semantic cache payload construction, dev-mode fetch normalization, and response shaping helpers.
- `resume_generation/bullet_points.py:99-132` - Routed project bullet generation through semantic cache keys and count-compatible cache reuse.
- `resume_generation/bullet_points.py:157-190` - Routed experience bullet generation through the same cache behavior.
- `tests/test_resume_generation.py:287-365` - Updated the shared successful pipeline fake to return the requested bullet count.
- `tests/test_resume_generation.py:938-1274` - Added regressions for project and experience cache reuse across dev/token-budget changes, count-compatible reuse, count-incompatible refresh, and evidence invalidation.

**Rationale:**
Bullet generation cache keys previously included presentation and execution fields, so changing `dev_mode` or `llm_max_output_tokens` caused avoidable LLM work. `bullet_count_range` is prompt-relevant on misses, but cached bullets can be reused safely when their existing count satisfies the current range. The new behavior keeps job context, evidence, evidence type, and model in the semantic key while validating count compatibility before accepting a cached result.

**Tests:**
- `test_project_bullet_cache_reuses_across_dev_mode_and_output_token_changes`: validates project bullets reuse cached content while shaping dev metadata for the current request.
- `test_experience_bullet_cache_reuses_across_dev_mode_and_output_token_changes`: validates equivalent experience bullet behavior.
- `test_project_bullet_cache_reuses_when_count_is_inside_requested_range`: validates broadening a range does not regenerate when cached count is still valid.
- `test_project_bullet_cache_refreshes_when_count_is_outside_requested_range`: validates a count-incompatible cached entry refreshes and is overwritten by a compatible result.
- `test_project_bullet_cache_invalidates_when_evidence_payload_changes`: validates evidence changes still miss the cache.
- `PYTHONPATH=. .venv/bin/pytest tests/test_resume_generation.py`: 53 passed.
- `PYTHONPATH=. .venv/bin/pytest`: 469 passed, 4 skipped.

**Impact:**
Project and experience bullet generation now avoid repeated LLM calls for debug and token-budget tweaks, while still regenerating when the target job, evidence, model, or required bullet count makes the cached result semantically unsuitable.
