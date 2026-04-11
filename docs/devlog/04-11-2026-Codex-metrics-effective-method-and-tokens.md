### 2026-04-11 - Track total tokens and fallback method usage

**Agent:** Codex (GPT-5)

**Changes:**
- `app/metrics.py` - Added cumulative `total_tokens` and `observe_tokens()`.
- `app/main.py` - Exposed `total_tokens` from `/metrics-lite`.
- `app/services/skill_selector.py` - Moved request counting until after scorer completion so fallback responses are counted under the effective method, and added total-token extraction from model metadata.
- `app/scoring/llm.py` - Added a generic `_fallback_method` marker to fallback metadata.
- `tests/test_integration.py` - Added coverage for metrics token totals and LLM-to-baseline fallback method usage.
- `README.md`, `docs/architecture-overview.md`, `docs/CHANGELOG.md` - Documented token metrics and effective method accounting.

**Rationale:**
Model-backed skill selection needs a service-level token counter for cost awareness. Method usage should reflect the method that actually produced the response; when an LLM request falls back to baseline, baseline is the effective method and should receive the usage increment.

**Tests:**
- `test_metrics_lite_includes_total_tokens`: validates the new metrics field.
- `test_select_skills_llm_success_increments_total_tokens`: verifies LLM token metadata increments the cumulative token counter even when dev details are hidden.
- `test_select_skills_llm_fallback_counts_baseline_usage`: verifies fallback responses increment baseline usage instead of LLM usage.

**Impact:**
Operators can now track aggregate LLM token cost from `/metrics-lite`, and method usage better reflects production behavior when fallback paths protect the service.
