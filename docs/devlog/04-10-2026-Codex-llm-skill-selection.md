### 2026-04-10 - Implement LLM skill selection

**Agent:** Codex (GPT-5)

**Changes:**
- `app/services/llm_client.py` - Added the single OpenAI Responses API wrapper for structured skill-score JSON, token usage metadata, API call count, and latency metadata.
- `app/scoring/llm.py` - Added LLM score validation, invented-skill and invalid-score filtering, deterministic local ranking, top-N slicing, and baseline fallback with dev warnings.
- `app/config.py`, `app/services/skill_selector.py`, `scripts/eval.py`, `app/models.py`, `app/main.py` - Added LLM configuration and `method="llm"` dispatch for the API and evaluation harness, including efficiency metadata extraction, widened dev metadata typing, and async ASGI-compatible route handlers.
- `app/scoring/baseline.py`, `app/services/embedding_client.py`, `app/services/embedding_cache.py` - Restored expected baseline debug metadata and made embedding helpers compatible with existing test stubs.
- `tests/test_llm.py`, `tests/test_llm_client.py`, `tests/test_integration.py` - Added unit and integration coverage for structured-output calls, local ranking, validation, subset guarantees, fallback, and API behavior.
- `tests/test_health.py`, `tests/conftest.py` - Kept API tests on ASGI transport and defaulted test runs to baseline unless explicitly overridden.
- `README.md`, `docs/architecture-overview.md`, `docs/CHANGELOG.md` - Documented the new LLM method and runtime settings.

**Rationale:**
The branch spec requires a pure LLM skill selector while preserving the existing API contract and baseline fallback guarantees. The implementation keeps outbound model calls in one service wrapper, validates all model output before ranking, and performs final ordering locally so stable deterministic ordering does not depend on model response order.

**Tests:**
- `test_score_skills_with_llm_sends_responses_schema`: verifies the Responses API wrapper sends the configured model and strict JSON schema and extracts token usage.
- `test_llm_select_skills_ranks_locally_with_normalized_tiebreak`: validates deterministic local sorting and original-casing output.
- `test_llm_select_skills_discards_invented_skills_and_unknown_categories`: ensures invented skills are not returned.
- `test_llm_select_skills_missing_category_falls_back_to_baseline`: validates baseline fallback on unusable model output.
- `test_select_skills_llm_method_returns_subset`: verifies the API path preserves response shape and subset compliance.
- `pytest`: validates the full suite without live OpenAI calls.
- `METHOD=llm OPENAI_API_KEY= PYTHONPATH=. .venv/bin/python scripts/eval.py -f eval_cases_basic.json`: verifies eval dispatch and baseline fallback for LLM mode when no key is configured.

**Impact:**
This unlocks `method="llm"` for skill selection experiments without adding resume generation, new skill categories, database dependencies, or scattered direct LLM calls. It also gives benchmark and dev-mode paths token and latency metadata for cost-aware evaluation.
