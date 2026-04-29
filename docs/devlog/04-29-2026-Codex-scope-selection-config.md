### 2026-04-29 - Scope selection runtime config

**Agent:** Codex (GPT-5)

**Changes:**
- `app/config.py:7-47` - Replaced generic selection settings with scoped `SKILL_*` and `PROJ_*` settings, split LLM defaults by subsystem, normalized configured method names, and ignored obsolete env keys.
- `app/skill_selection/selector.py:92-140` and `app/project_selection/service.py:53-89` - Resolved request overrides against scoped settings and added subsystem fields to structured selector logs.
- `app/skill_selection/llm_client.py:163-195` and `app/project_selection/llm_client.py:132-165` - Routed LLM client model and output-token settings through subsystem-specific config.
- `app/main.py:28-48` - Replaced generic health config keys with scoped `skill_selection` and `project_selection` blocks.
- `tests/test_config.py:1-89`, `tests/test_baseline_filter.py:64-84`, and `tests/test_project_selection_api.py:62-87` - Added coverage for scoped defaults, method validation, ignored legacy env vars, and request/config precedence.
- `README.md:136-310`, `docs/architecture-overview.md`, `docs/Embedding.md`, `scripts/README.md`, and `scripts/eval.py` - Updated public configuration docs and skill eval usage to the scoped setting names.
- `docs/decisions/006-scoped-selection-runtime-config.md` and `docs/CHANGELOG.md:8-13` - Recorded the runtime config decision and the breaking config change.

**Rationale:**
Generic selection config made skill-selection options look application-wide after project selection was added. The scoped settings make skill and project selection parallel where they are actually parallel, while keeping `baseline_filter` skill-only until project selection has a real two-pass algorithm.

**Tests:**
- `PYTHONPATH=. .venv/bin/python -m pytest`: validates the full test suite.
- `SKILL_METHOD=baseline PYTHONPATH=. .venv/bin/python scripts/eval.py -f eval_cases_basic.json`: validates skill eval dispatch with the new setting name.
- `PYTHONPATH=. .venv/bin/python docs/agentic-testing/run_agentic_dataset.py --suite all --dry-run`: validates the agentic dataset runner still builds endpoint-local request payloads.

**Impact:**
Deployments now configure skill and project selection independently. Legacy generic env vars are no longer honored, `/health` exposes scoped config, and future project-selection tuning no longer has to borrow skill-selection names.
