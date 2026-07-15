### 2026-07-15 - Skill LLM Retry Cache Logging

**Agent:** Codex (GPT-5)

**Changes:**
- `app/skill_selection/llm_client.py:19-360` - Added retry-aware skill LLM scoring with dynamic default output caps, per-attempt token metadata, and carried `LLMClientError` metadata.
- `app/skill_selection/scoring/llm.py:18-162` - Preserved failed LLM usage metadata in baseline fallback details.
- `app/main.py:88-99` and `app/skill_selection/selector.py:137-172` - Logged request-level `llm_max_output_tokens` for skill-selection requests and failures.
- `resume_generation/cache.py:19-105` and `resume_generation/selection.py:107-204` - Added conditional stage cache storage and skipped caching skill-selection responses whose LLM path fell back to baseline.
- `tests/test_llm_client.py:145-259`, `tests/test_llm.py`, `tests/test_integration.py`, `tests/test_resume_generation.py:1815-1939`, and `tests/test_config.py` - Added retry, fallback metadata, metrics, cache-skip, request logging, and config validation coverage.

**Rationale:**
The token efficiency audit found that truncated skill LLM calls could fall back to baseline, hide failed-call token spend, and persist the degraded result in the resume-generation cache. The fix follows the existing bullet-generation retry pattern while keeping explicit baseline selection cacheable and deterministic.

**Tests:**
- `test_score_skills_with_llm_retries_malformed_json`: validates retry with a larger output budget and aggregated usage.
- `test_score_skills_with_llm_error_carries_failed_attempt_metadata`: validates failed attempts retain usage and attempted caps.
- `test_select_skills_llm_fallback_counts_baseline_usage`: validates fallback token usage is still counted when details are hidden.
- `test_resume_generation_pipeline_does_not_cache_skill_llm_fallback`: validates degraded LLM fallback responses are not persisted and request caps are logged.
- `PYTHONPATH=. pytest tests/test_llm_client.py tests/test_llm.py tests/test_integration.py tests/test_config.py`
- `PYTHONPATH=. pytest tests/test_resume_generation.py -q`

**Impact:**
Skill LLM truncation can recover automatically, failed LLM token usage remains observable through fallback metadata, and resume generation no longer reuses cached baseline fallback results for requested LLM skill selection.
