### 2026-05-21 - Modern CLI Selection UI

**Agent:** Codex (GPT-5)

**Changes:**
- `app/resume_evidence/selection_ui.py:1-31` - Added a reusable `prompt_toolkit` picker adapter that returns one-based indices and gracefully returns `None` when unavailable or canceled.
- `app/resume_evidence/projects_cli.py:12-328` - Added injectable picker support, optional-index project `show`/`edit`/`delete`, optional-index highlight `edit`/`delete`, updated help text, and fallback guidance for non-interactive command use.
- `requirements.txt:21-39` - Added `prompt_toolkit==3.0.52` and pinned its `wcwidth==0.7.0` runtime dependency.
- `tests/test_resume_evidence_cli.py:112-580` - Added deterministic fake-picker coverage for project selection, highlight selection, cancellation, and non-interactive fallback.
- `docs/decisions/007-modern-cli-selection-ui.md:5-65` - Marked ADR 007 accepted and documented the scoped optional-index implementation.
- `docs/CHANGELOG.md:10-12` - Added the user-facing CLI picker feature to the unreleased changelog.

**Rationale:**
The implementation keeps the existing command REPL as the stable baseline while making repeated project and highlight selection smoother in interactive terminals. The picker is injected for tests and isolated behind a small adapter so prompt-toolkit behavior does not leak into session logic or deterministic command tests.

**Tests:**
- `test_cli_show_without_index_uses_project_picker`: validates no-index project show selection.
- `test_cli_edit_without_index_uses_project_picker`: validates no-index project edit selection and persisted staged updates.
- `test_cli_delete_without_index_uses_project_picker`: validates no-index project deletion.
- `test_cli_edit_highlight_without_index_uses_picker`: validates highlight picker editing.
- `test_cli_delete_highlight_without_index_uses_picker`: validates highlight picker deletion.
- `test_cli_project_picker_cancellation_leaves_staged_data_unchanged`: validates picker cancellation containment.
- `test_cli_project_picker_unavailable_falls_back_to_index_guidance`: validates non-interactive fallback guidance.

**Impact:**
Users can now run `show`, `edit`, or `delete` without memorizing indices in interactive projects CLI sessions, while scripts and non-interactive test flows can continue using explicit numeric indices.
