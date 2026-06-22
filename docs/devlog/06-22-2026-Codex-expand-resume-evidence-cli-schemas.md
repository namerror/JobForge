### 2026-06-22 - Expand resume evidence CLI schemas

**Agent:** Codex (GPT-5)

**Changes:**
- `resume_evidence/cli/` - Moved CLI components into a standalone package with schema dispatch, shared prompt helpers, selection UI helpers, and schema-specific command modules.
- `resume_evidence/session.py` - Added staged sessions and pending-change reporting for education, experience, and user info evidence.
- `tests/test_resume_evidence_cli.py` - Added session and CLI coverage for education, experience, and user workflows.
- `README.md`, `docs/architecture-overview.md`, `docs/branch-03-grounded-resume-generation.md`, `docs/agent-context-index.md`, `docs/CHANGELOG.md` - Updated CLI and schema documentation.

**Rationale:**
The existing projects and skills CLI established a staged edit/apply/reload safety model. Education and experience are list schemas, so they now get full CRUD workflows. User info is a singleton contact schema, so it gets show/edit/apply/reload/quit commands without forcing list-style commands onto it.

**Tests:**
- `test_education_session_*`: validates staged education CRUD, apply, and invalid edit rollback.
- `test_experience_session_*`: validates staged experience CRUD, stable IDs across rename, and apply.
- `test_user_info_session_*`: validates staged user info edits, apply, and invalid edit rollback.
- `test_*_cli_*`: validates list/show/create/edit/delete/apply/reload/quit behavior for the new schema CLIs.

**Impact:**
Users can now manage every registered resume evidence schema through `python -m resume_evidence.cli --schema <schema>`, and future CLI components have a clear package boundary under `resume_evidence/cli/`.
