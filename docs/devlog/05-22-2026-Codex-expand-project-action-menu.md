### 2026-05-22 - Expand project action menu

**Agent:** Codex (GPT-5)

**Changes:**
- `app/resume_evidence/projects_cli.py:11-19` - Expanded the top-level project action menu to include every help-listed command except `help`: `list`, `show`, `edit`, `create`, `delete`, `apply`, `reload`, and `quit`.
- `tests/test_resume_evidence_cli.py:344-548` - Updated menu expectations and added coverage for menu-dispatched `list`, `show`, `apply`, and `reload`.
- `docs/CHANGELOG.md:10` - Updated the unreleased CLI entry to describe the command-complete action menu.

**Rationale:**
After a menu-driven edit, users need an immediate menu path to save staged changes. Routing `apply` and the other help-listed commands through the same raw command dispatcher keeps the menu broad enough for the normal workflow without duplicating command logic.

**Tests:**
- `test_projects_cli_action_menu_list_matches_list_command`: validates menu `list` dispatch.
- `test_projects_cli_action_menu_show_matches_show_command`: validates menu `show` uses the existing project picker path.
- `test_projects_cli_action_menu_apply_saves_after_menu_edit`: validates edited staged changes can be saved from the menu before quitting.
- `test_projects_cli_action_menu_reload_matches_reload_command`: validates menu `reload` uses existing dirty confirmation and reload behavior.
- `.venv/bin/python -m pytest tests/test_resume_evidence_cli.py`: 49 passed.

**Impact:**
The projects CLI menu now supports the full non-help command workflow, so picker-first editing no longer strands users before applying pending changes.
