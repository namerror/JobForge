### 2026-06-05 - Load Resume Evidence In Generation Pipeline

**Agent:** Codex (GPT-5)

**Changes:**
- `resume_generation/selection.py:9-120` - Removed stage-level evidence loading from `generate_selection_context(...)` and made already-loaded evidence a required input.
- `resume_generation/main.py:3-13` - Loaded registered resume evidence once in the pipeline entrypoint and passed it into selection-context generation.
- `tests/test_resume_generation.py:22-270` - Updated orchestration tests to pass validated evidence objects directly and fail if the selection stage attempts to reload evidence.

**Rationale:**
Evidence should be loaded once by the resume-generation pipeline and kept in memory for later stages instead of being reloaded inside each stage. Keeping `generate_selection_context(...)` focused on adapting in-memory evidence to selection requests makes the generation pipeline responsible for evidence lifecycle while preserving the existing HTTP selection boundary.

**Tests:**
- `test_generate_selection_context_posts_evidence_payloads`: validates selection context generation uses passed-in evidence, posts expected skill/project payloads, filters inactive projects, and does not reload evidence internally.
- `test_generate_selection_context_wraps_http_errors`: validates HTTP failures are still wrapped when evidence is supplied by the caller.
- `.venv/bin/python -m pytest tests/test_resume_generation.py tests/test_resume_evidence.py`: 33 passed.

**Impact:**
The resume-generation entrypoint now owns initial evidence loading, enabling later pipeline stages to reuse the same validated evidence objects without repeated disk reads.
