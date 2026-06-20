### 2026-06-20 - Add Resume Generation Stage Cache

**Agent:** Codex (GPT-5)

**Changes:**
- `resume_generation/models.py:173-198` - Added cache configuration for enabling stage caching, custom cache paths, and force refresh.
- `resume_generation/cache.py:18-128` - Added a JSON-on-disk stage cache with exact payload hashing and atomic writes.
- `resume_generation/selection.py:99-167` - Routed skill and project selection HTTP calls through the optional cache.
- `resume_generation/link_scanning.py:17-57` and `resume_generation/bullet_points.py:17-54` - Added per-project cache support for link scanning and bullet generation.
- `resume_generation/main.py:30-77` - Builds one cache instance from config and passes it through the pipeline.
- `user/resume_generation/config.yaml` - Enabled the default resume-generation cache under `user/resume_generation/cache/`.
- `.gitignore` - Ignored generated resume-generation cache artifacts.
- `docs/decisions/010-resume-generation-stage-cache.md` - Recorded the stage-output cache architecture.
- `tests/test_resume_generation.py:234-335` and `tests/test_resume_generation.py:1057-1365` - Added cache config, cache helper, cache reuse, invalidation, and resume-after-failure coverage.

**Rationale:**
The cache is keyed from the exact outgoing request payload for each expensive stage, so changes to job target, evidence, or generation settings automatically produce misses. Per-project caching for link scanning and bullet generation is necessary to resume after a failure without repeating completed project-level LLM calls.

**Tests:**
- `test_resume_generation_stage_cache_reuses_exact_payload`: validates deterministic cache hits independent of dict key order.
- `test_resume_generation_stage_cache_invalidates_changed_payload`: validates exact payload changes miss.
- `test_resume_generation_stage_cache_force_refresh_bypasses_read`: validates refresh recomputes and overwrites cached data.
- `test_resume_generation_stage_cache_treats_malformed_entry_as_miss`: validates malformed JSON does not block recovery.
- `test_resume_generation_pipeline_reuses_cached_stage_results`: validates reruns skip cached HTTP stage calls.
- `test_resume_generation_pipeline_cache_misses_when_job_target_changes`: validates job-target edits invalidate pipeline stage entries.
- `test_resume_generation_pipeline_resumes_after_project_bullet_failure`: validates a failed per-project bullet step can resume without repeating earlier successful stages.
- `PYTHONPATH=. .venv/bin/python -m pytest tests/test_resume_generation.py`: 26 passed.

**Impact:**
Resume generation can now recover from interrupted or failed LLM-backed stages while avoiding repeated token spend for already-completed work.
