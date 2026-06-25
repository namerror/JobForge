### 2026-06-25 - Add experience CLI selection editor

**Agent:** Codex (GPT-5)

**Changes:**
- `resume_evidence/cli/experience.py:7-380` - Added project-style action picker support, optional-index `show`/`edit`/`delete`, and a nested indexed highlight editor for experience entries.
- `tests/test_resume_evidence_cli.py:18-281` - Added injectable experience CLI test helpers using fake entry and action pickers.
- `tests/test_resume_evidence_cli.py:1506-1818` - Added experience CLI coverage for action menu dispatch, typed fallback, picker-based entry selection, indexed highlight edits, add/delete, final-highlight protection, and recoverable nested command errors.
- `docs/CHANGELOG.md` - Documented the user-facing experience CLI editing improvement.

**Rationale:**
Experience evidence has the same summary/highlights/skills editing needs as project evidence, but it was still using required numeric commands and full-list highlight replacement. Mirroring the project CLI keeps the staged session model intact while making small experience highlight edits practical and preserving comma-containing evidence text.

**Tests:**
- `test_experience_cli_action_menu_show_uses_entry_picker`: validates action-menu dispatch and picker-based entry selection.
- `test_experience_cli_*_without_index_uses_picker`: validates optional-index show/edit/delete behavior.
- `test_experience_cli_edit_*highlight*`: validates indexed highlight editing, picker selection, add/delete, final-highlight protection, and recoverable nested errors.
- `python -m pytest tests/test_resume_evidence_cli.py`: validates all resume evidence CLI coverage.
- `python -m pytest`: validates the full repository suite.

**Impact:**
Experience evidence editing now matches the faster project editing workflow. Users can select entries and edit individual highlights without retyping every highlight, while deterministic YAML validation and staged apply/reload behavior remain unchanged.
