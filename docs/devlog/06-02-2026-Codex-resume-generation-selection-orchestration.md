### 2026-06-02 - Resume Generation Selection Orchestration

**Agent:** Codex (GPT-5)

**Changes:**
- `resume_generation/models.py:15-154` - Added strict config, job target, service response, and selection-context models for the first generation workflow.
- `resume_generation/config.py:12-31` - Added default `user/resume_generation` paths and YAML loaders for generation config and job target files.
- `resume_generation/selection.py:33-161` - Added evidence-to-HTTP payload adapters, HTTP error wrapping, and `generate_selection_context(...)`.
- `app/skill_selection/models.py:15-16` and `app/project_selection/models.py:67-68` - Added optional per-request LLM model and token-budget overrides.
- `app/skill_selection/llm_client.py:127-208` and `app/project_selection/llm_client.py` - Threaded request-level LLM overrides through client calls while preserving `.env` settings as defaults.
- `user/resume_generation/config.yaml` and `user/resume_generation/job_target.yaml` - Added user-level generation defaults for app HTTP settings, selection options, and target job context.
- `tests/test_resume_generation.py:111-354` - Added loader, adapter, orchestration, error wrapping, and API override propagation tests.
- `docs/architecture-overview.md`, `docs/agent-context-index.md`, `README.md`, and `docs/CHANGELOG.md` - Documented the implemented generation selection layer.

**Rationale:**
The generation layer should own evidence-to-selection orchestration without importing app service functions directly. Posting explicit request payloads lets user-level generation YAML take precedence over app environment defaults for supported options, while preserving the existing FastAPI service boundary.

**Tests:**
- `test_load_generation_config_returns_typed_config`: validates strict config loading and typed nested settings.
- `test_build_skill_selection_payload_uses_evidence_and_config`: validates evidence and user config are combined into the `/select-skills` payload.
- `test_generate_selection_context_posts_evidence_payloads`: validates HTTP endpoint order, active-project filtering, request overrides, and typed result assembly.
- `test_skill_selection_api_uses_request_llm_overrides`: validates skill LLM request overrides reach the scorer client.
- `test_project_selection_api_uses_request_llm_overrides`: validates project LLM request overrides reach the scorer client.
- Full suite: `PYTHONPATH=. pytest` passed with 285 passed and 4 skipped.

**Impact:**
This enables the first callable resume-generation workflow: load grounded evidence, load user-level generation settings, call skill/project selection over HTTP, and return structured selection context for later synthesis and deterministic assembly.
