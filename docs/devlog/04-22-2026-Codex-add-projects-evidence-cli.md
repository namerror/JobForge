### 2026-04-22 - Add staged projects evidence CLI

**Agent:** Codex (GPT-5)

**Changes:**
- `app/resume_evidence/session.py:26-219` - Added the reusable projects evidence session layer with hidden slug ID generation, staged in-memory CRUD, validation-before-mutation, pending-change summaries, reload support, and atomic apply-to-disk behavior.
- `app/resume_evidence/cli.py:12-327` - Added the interactive REPL entrypoint for `python -m app.resume_evidence.cli` with `list`, `show`, `create`, `edit`, `delete`, `apply`, `reload`, and `quit`.
- `app/resume_evidence/__init__.py:1-25` - Exported the new session helpers from the package surface.
- `tests/test_resume_evidence_cli.py:13-306` - Added session and REPL coverage for staged edits, explicit apply confirmation, reload/quit discard behavior, hidden IDs, and custom `--path` usage.
- `docs/CHANGELOG.md:10-11` - Added the new user-facing CLI feature to the unreleased changelog.

**Rationale:**
The current milestone only needs local CRUD around `projects.yaml`, so I kept the implementation file-based and avoided adding any HTTP or FastAPI coupling. The session object centralizes the critical rule that edits mutate only a staged in-memory copy until the user explicitly confirms `apply`, which keeps the REPL simple and makes the behavior directly testable.

**Tests:**
- `test_session_create_stages_changes_without_writing_file`: verifies staged create does not touch disk before apply.
- `test_session_update_keeps_original_id_on_rename`: verifies auto-generated IDs stay stable after rename.
- `test_session_rejects_invalid_edit_without_mutating_staged_state`: verifies invalid changes are rejected without corrupting the staged document.
- `test_session_apply_writes_schema_valid_yaml_and_clears_dirty_flag`: verifies atomic apply persists valid YAML and resets dirty state.
- `test_cli_create_stages_changes_without_persisting_before_apply`: verifies REPL create stages data but does not persist it.
- `test_cli_apply_requires_confirmation_before_writing`: verifies `apply` requires explicit confirmation.
- `test_cli_reload_discards_dirty_changes_only_after_confirmation`: verifies reload discard flow.
- `test_cli_quit_warns_about_unapplied_changes`: verifies quit warning behavior when the staged copy is dirty.

**Impact:**
This adds a usable first interface for resume evidence management without exposing internal IDs or forcing users to hand-edit YAML. It also establishes a reusable staged-edit pattern the repo can later extend to other evidence files without changing the persisted schema.
