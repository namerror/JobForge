### 2026-05-22 - Remove project menu Back key

**Agent:** Codex (GPT-5)

**Changes:**
- `app/resume_evidence/selection_ui.py:45-57` - Removed the custom Escape key binding from the reusable value picker and changed the toolbar copy to direct users to Ctrl+C for typed command mode.
- `app/resume_evidence/projects_cli.py:11-16` - Removed the visible Back option from the top-level project action menu.
- `tests/test_resume_evidence_cli.py:351-476` - Updated action-menu expectations and renamed the cancellation test to cover picker cancellation rather than a Back option.
- `docs/CHANGELOG.md:10` - Updated the user-facing menu entry to describe Ctrl+C fallback instead of Back.

**Rationale:**
The Escape binding was unreliable in the current prompt-toolkit menu. Relying on the library's existing Ctrl+C interrupt path keeps cancellation simpler while preserving typed-command fallback.

**Tests:**
- `test_projects_cli_action_menu_lists_projects_at_startup`: validates the menu no longer includes Back.
- `test_projects_cli_action_menu_cancellation_returns_to_typed_prompt`: validates cancellation still returns to typed commands without mutating evidence.
- `.venv/bin/python -m pytest tests/test_resume_evidence_cli.py`: 45 passed.

**Impact:**
The top-level project menu has fewer custom key bindings and a clearer escape hatch to command-line mode.
