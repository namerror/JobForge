### 2026-06-08 - Resume Generation Pipeline Modularization

**Agent:** Codex (GPT-5)

**Changes:**
- `resume_generation/main.py:10-55` - Moved pipeline-level config, job target, and evidence loading into `run_resume_generation_pipeline(...)`.
- `resume_generation/selection.py:92-159` - Changed selection orchestration to accept already-loaded `ResumeGenerationConfig` and `JobTarget` objects.
- `resume_generation/bullet_points.py:1-44` - Added a dedicated bullet-point generation module for `/generate-bulletpoints` orchestration.
- `tests/test_resume_generation.py` - Updated selection and bullet generation tests for the new module boundaries and added pipeline coverage.
- `docs/agent-context-index.md`, `docs/architecture-overview.md`, `README.md`, `docs/CHANGELOG.md` - Refreshed stale orchestration ownership descriptions.

**Rationale:**
The generation pipeline should load shared inputs once and pass typed objects to individual stages. This keeps `resume_generation/main.py` responsible for orchestration while `selection.py` and `bullet_points.py` focus on their API payload and response handling.

**Tests:**
- `test_generate_selection_context_posts_evidence_payloads`: validates selection still posts the expected skill and project payloads using passed-in config and job target data.
- `test_generate_project_bullet_points_posts_once_per_selected_project`: validates bullet-point payload shape and config propagation from the new module.
- `test_resume_generation_pipeline_loads_config_job_and_evidence_once`: validates the pipeline coordinates selection and bullet generation from the main boundary.
- `PYTHONPATH=. pytest tests/test_resume_generation.py`

**Impact:**
This removes duplicate config and job target loading across generation stages and leaves room for additional resume generation modules without growing `main.py` beyond pipeline coordination.
