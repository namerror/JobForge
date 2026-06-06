### 2026-06-06 - Bullet Point Generation Orchestration

**Agent:** Codex (GPT-5)

**Changes:**
- `resume_generation/models.py:100-214` - Added bullet-point generation config validation and a typed per-project result model.
- `resume_generation/main.py:3-73` - Implemented `bullet_point_generation(...)` to load config/job target data, resolve selected projects, and call `/generate-bulletpoints` once per project.
- `resume_generation/__init__.py` - Exported the new config and result models.
- `user/resume_generation/config.yaml:18-23` - Added bullet-point generation runtime defaults.
- `tests/test_resume_generation.py` - Added config validation, per-project request, missing-id skip, and HTTP error coverage.

**Rationale:**
The resume generation pipeline already calls selection services through the FastAPI app boundary. This keeps bullet generation on the same boundary, reuses the existing app HTTP settings, and adds only the config surface needed by the existing `/generate-bulletpoints` API.

**Tests:**
- `test_load_generation_config_returns_typed_config`: validates bullet generation config loading.
- `test_load_generation_config_rejects_invalid_bullet_count_range`: validates count range constraints before requests are made.
- `test_bullet_point_generation_posts_once_per_selected_project`: validates payload shape, config propagation, ordering, and missing-id skip behavior.
- `test_bullet_point_generation_wraps_http_errors`: validates endpoint failures become `ResumeGenerationError`.
- `.venv/bin/python -m pytest tests/test_resume_generation.py`: 10 passed.

**Impact:**
Selected project evidence can now be sent to the bullet-point generation API as a minimal orchestration step, producing structured project-id-to-bullets results for later resume draft assembly.
