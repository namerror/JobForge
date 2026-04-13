### 2026-04-13 - Baseline-filtered skill selection

**Agent:** Codex (GPT-5)

**Changes:**
- `app/models.py:5-14` - Added the optional `baseline_filter` request field.
- `app/config.py:26-32` and `app/main.py:65-73` - Added `BASELINE_FILTER` settings support and exposed it on `/health`.
- `app/services/baseline_filter.py:15-299` - Added baseline-filter orchestration for recognized/unrecognized splitting, score normalization, deterministic merging, warning propagation, and full-baseline fallback.
- `app/services/skill_selector.py:47-156` - Kept direct scorer dispatch, request/config precedence, effective-method metrics, token extraction, and response shaping in the primary service module.
- `scripts/eval.py:14-16` and `scripts/eval.py:90-187` - Routed eval selection through the production service, added baseline-filter overrides, and included `baseline_filter` in eval output.
- `tests/test_baseline_filter.py:38-346` - Added focused unit, API, metrics, token, fallback, and eval override coverage for baseline filtering.
- `README.md`, `scripts/README.md`, `docs/architecture-overview.md`, and `docs/CHANGELOG.md` - Documented the new request/config option, eval flags, request flow, and user-facing changelog entry.
- `docs/decisions/002-baseline-filter-selection.md` - Recorded the API/config, normalization, and fallback decisions.

**Rationale:**
Branch 01 needed an opt-in two-pass selection flow without introducing a new public method. Keeping `baseline_filter` as a request/config flag preserves existing `baseline`, `embeddings`, and `llm` semantics while allowing deterministic role-profile hits to be handled before model-backed scoring.

The baseline-filter logic now lives in `app/services/baseline_filter.py` so `skill_selector.py` remains the top-level service dispatcher and metrics wrapper rather than also owning the merge algorithm.

The fallback behavior intentionally returns a full baseline selection over the original request. This keeps the baseline path as the safe system default if embeddings or LLM scoring fails after the pre-filter.

**Tests:**
- `test_baseline_filter_false_preserves_selected_method_behavior`: verifies opt-out behavior still calls the selected scorer directly.
- `test_baseline_method_treats_baseline_filter_as_noop`: verifies baseline ignores the filter flag.
- `test_baseline_filter_sends_only_unrecognized_skills_to_second_pass`: verifies recognized skills stay with baseline and only zero-score skills go to the model-backed scorer.
- `test_baseline_filter_final_ranking_is_deterministic_after_merge`: validates final normalized score ordering and deterministic tie-breaking.
- `test_baseline_filter_skips_second_pass_when_all_skills_are_recognized`: verifies no unnecessary model-backed call.
- `test_baseline_filter_embedding_failure_returns_full_baseline` and `test_baseline_filter_llm_fallback_metadata_returns_full_baseline_and_tokens`: verify fallback metadata and token preservation.
- `test_select_skills_accepts_baseline_filter_and_keeps_default_shape`, `test_health_includes_baseline_filter`, `test_baseline_filter_fallback_counts_baseline_usage`, and `test_baseline_filter_llm_success_increments_total_tokens`: cover API shape, health output, effective-method metrics, and hidden token metadata.
- `test_eval_includes_and_passes_baseline_filter_override`: verifies eval override plumbing.
- `PYTHONPATH=. .venv/bin/pytest -q`: 160 passed, 4 skipped.
- `PYTHONPATH=. .venv/bin/python scripts/eval.py -f eval_cases_basic.json`: exited 0; active `.env` uses `METHOD=llm`, so restricted network access caused LLM fallback to baseline.
- `BASELINE_FILTER=true PYTHONPATH=. .venv/bin/python scripts/eval.py -f eval_cases_basic.json`: exited 0 with `baseline_filter: true`; active `.env` uses `METHOD=llm`, so restricted network access caused LLM fallback to baseline.
- `METHOD=baseline PYTHONPATH=. .venv/bin/python scripts/eval.py -f eval_cases_basic.json`: exited 0 after extracting `app/services/baseline_filter.py`.
- `METHOD=baseline BASELINE_FILTER=true PYTHONPATH=. .venv/bin/python scripts/eval.py -f eval_cases_basic.json`: exited 0 after extracting `app/services/baseline_filter.py`.

**Impact:**
Callers can now opt into baseline-filtered embeddings or LLM scoring without changing the public method set. Evaluation output can compare filtered and unfiltered runs, and model-backed failures continue to return deterministic baseline results.
