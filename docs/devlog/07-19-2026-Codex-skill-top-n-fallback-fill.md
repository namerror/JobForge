### 2026-07-19 - Skill top_n fallback fill

**Agent:** Codex (GPT-5)

**Changes:**
- `app/skill_selection/scoring/llm.py:30-39` - Changed LLM scoring fallback to baseline selection with zero-score skills included, so fallback can still satisfy the requested per-category count when enough candidate skills exist.
- `app/skill_selection/baseline_filter.py:119-128` - Applied the same zero-score inclusion to full baseline-filter fallback.
- `resume_generation/selection.py:210-244` - Reused the fallback detection rule for cached response reads, not only cache writes.
- `resume_generation/selection.py:373-418` - Made skill and project selection cache reads bypass stale baseline-fallback responses.
- `tests/test_llm.py:188-211` - Added coverage for LLM fallback filling `top_n` with deterministic zero-score skills.
- `tests/test_resume_generation.py:2977-3087` - Added coverage for bypassing old cached skill-selection fallback responses.

**Rationale:**
`top_n` is intended to act as the requested number of selected skills per category, bounded by the number of user-provided skills. LLM scoring already asks the model to score every candidate, including zero-relevance skills, but malformed LLM responses fell back to baseline selection that dropped zero-score items. Resume-generation caching could also keep reusing older fallback entries even after fallback storage was disabled.

**Tests:**
- `test_llm_fallback_fills_top_n_with_zero_score_skills`: validates that LLM fallback returns the requested count using deterministic zero-score tail items.
- `test_selection_context_bypasses_cached_skill_llm_fallback`: validates that stale cached fallback selection responses are ignored and refreshed through HTTP.
- `.venv/bin/python -m pytest tests/test_llm.py tests/test_resume_generation.py -q`: 73 passed.

**Impact:**
Resume generation now treats `skill_selection.top_n` as an exact requested count where possible for LLM-backed runs, even when LLM scoring falls back. Existing stale fallback caches no longer silently cap the final Skills section to only baseline-positive matches.
