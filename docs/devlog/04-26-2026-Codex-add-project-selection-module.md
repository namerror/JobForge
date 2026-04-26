### 2026-04-26 - Add internal project selection module

**Agent:** Codex (GPT-5)

**Changes:**
- `app/project_selection/models.py:11-29` - Added internal project-selection request/result models.
- `app/project_selection/selector.py:42-71` - Added the `select_projects(...)` entrypoint with method dispatch, duplicate-ID validation, and `top_n` validation.
- `app/project_selection/baseline.py:85-204` - Added deterministic project ranking from baseline skill matches and summary/job text overlap.
- `app/project_selection/llm.py:30-152` - Added LLM score validation, local ranking, and baseline fallback behavior.
- `app/services/project_llm_client.py:28-164` - Added a dedicated OpenAI Responses API wrapper for project relevance scoring.
- `tests/test_project_selection_baseline.py` - Added deterministic baseline project-ranking coverage.
- `tests/test_project_selection_llm.py` - Added LLM selector validation and fallback coverage.
- `tests/test_project_llm_client.py` - Added project LLM client schema, payload, and error-path coverage.
- `docs/project-selection-plan.md`, `docs/architecture-overview.md`, `docs/agent-context-index.md` - Documented the internal project-selection milestone and navigation entry points.

**Rationale:**
Project selection is the next small Branch 03 step toward grounded resume generation. The implementation stays internal, accepts explicit candidates for testability, reuses the existing skill taxonomy, and keeps evidence loading separate from ranking. The LLM path follows the skill selector pattern: model scores are only an input to local validation/ranking, and deterministic baseline selection remains the fallback.

**Tests:**
- `test_baseline_project_selection_is_skill_heavy_over_text_overlap`: validates the skill-heavy baseline blend.
- `test_baseline_project_selection_top_match_aggregation_ignores_extra_irrelevant_skills`: validates top-match aggregation.
- `test_llm_project_selection_discards_invented_ids_and_invalid_scores`: validates local LLM response filtering.
- `test_llm_project_selection_falls_back_to_baseline_on_client_failure`: validates deterministic fallback behavior.
- `test_score_projects_with_llm_sends_strict_project_schema`: validates the dedicated project LLM client request shape.

**Impact:**
Branch 03 now has a reusable project-ranking layer that future synthesis can call before assembling resume sections. It ranks grounded project evidence without generating unsupported project claims or changing the public API surface.
