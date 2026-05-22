### 2026-05-22 - Add project CLI action menu

**Agent:** Codex (GPT-5)

**Changes:**
- `app/resume_evidence/selection_ui.py:7-66` - Added a reusable value picker that can return command values, supports an explicit `None` back/cancel result, and binds Escape to exit the menu.
- `app/resume_evidence/projects_cli.py:11-69` - Added a top-level project action menu with edit/create/delete/quit/Back choices, startup project listing, typed-command fallback, and shared command error handling.
- `tests/test_resume_evidence_cli.py:125-486` - Added deterministic fake action-picker coverage for startup listing, menu-dispatched edit/create/delete/quit, Back behavior, and non-interactive typed-command fallback.
- `docs/CHANGELOG.md:10` - Documented the user-facing project action menu.

**Rationale:**
The menu translates user selections into existing commands instead of duplicating CRUD behavior, keeping staged session logic and validation untouched. A separate injectable action picker preserves existing project/highlight picker tests and gives future CLI menus a small reusable abstraction.

**Tests:**
- `test_projects_cli_action_menu_lists_projects_at_startup`: validates startup project listing and menu options, including Back.
- `test_projects_cli_action_menu_edit_matches_edit_command`: validates menu edit dispatches through the existing edit flow.
- `test_projects_cli_action_menu_create_matches_create_command`: validates menu create dispatches through the existing create flow.
- `test_projects_cli_action_menu_delete_matches_delete_command`: validates menu delete dispatches through the existing delete flow.
- `test_projects_cli_action_menu_quit_uses_existing_dirty_confirmation`: validates menu quit uses the existing dirty-change confirmation.
- `test_projects_cli_action_menu_back_returns_to_typed_prompt`: validates Back returns to typed commands without mutating evidence.
- `test_projects_cli_without_action_picker_still_accepts_typed_commands`: validates non-interactive fallback remains scriptable.
- `.venv/bin/python -m pytest tests/test_resume_evidence_cli.py`: 45 passed.

**Impact:**
The projects CLI now starts from a picker-first workflow in interactive terminals while preserving command-mode ergonomics for scripts, tests, and fallback environments.
