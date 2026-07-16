### 2026-07-16 - Selection cache key normalization

**Agent:** Codex (GPT-5)

**Changes:**
- `resume_generation/cache.py:54-91` - Added an optional `cache_payload` so callers can use a semantic cache key while keeping the actual fetch payload available to the HTTP call.
- `resume_generation/selection.py:31-132` - Added selection cache-key normalization, all-candidate canonical fetch payloads, and local response shaping for `top_n` and `dev_mode`.
- `resume_generation/selection.py:210-320` - Extended selection fallback cache skipping to project selection and wired `_cached_post_json` to use separate fetch and cache payloads.
- `resume_generation/selection.py:353-402` - Routed skill and project selection through semantic cache payloads when the stage cache is enabled.
- `tests/test_resume_generation.py:472-493` - Added coverage for semantic cache payload lookup.
- `tests/test_resume_generation.py:1877-2020` - Added selection-cache reuse coverage across `top_n`, `dev_mode`, and `llm_max_output_tokens` changes.
- `tests/test_resume_generation.py:2162-2262` - Added project LLM fallback cache-skip coverage.

**Rationale:**
Selection endpoints score and rank the full candidate set before response shaping. The resume-generation cache previously keyed the whole endpoint request, so local controls such as `top_n`, `dev_mode`, and output-token budget changes caused avoidable LLM work. The new path stores reusable full selection responses under a semantic key and re-applies presentation choices locally.

**Tests:**
- `test_resume_generation_stage_cache_uses_cache_payload_for_lookup`: validates `cache_payload` controls lookup while fetch still sees the original payload through the closure.
- `test_selection_cache_reuses_scores_across_response_shaping_fields`: validates selection HTTP calls are reused when only `top_n`, `dev_mode`, and `llm_max_output_tokens` change.
- `test_selection_cache_does_not_store_project_llm_fallback`: validates project LLM fallback responses are treated as non-cacheable.
- `PYTHONPATH=. .venv/bin/pytest tests/test_resume_generation.py`: 48 passed.
- `PYTHONPATH=. .venv/bin/pytest`: 464 passed, 4 skipped.

**Impact:**
Resume generation can now reuse successful skill and project selection results across presentation and token-budget tweaks, reducing repeated LLM calls while preserving deterministic local slicing and debug metadata visibility.
