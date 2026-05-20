### 2026-05-20 - Refine Resume Evidence CLI Editing

**Agent:** Codex (GPT-5)

**Changes:**
- `app/resume_evidence/base_cli.py:75-164` - Added comma-separated list prompting/parsing for skill categories, strict empty-segment validation, and interactive readline prefill for default text values.
- `app/resume_evidence/projects_cli.py:94-127` - Switched project skill create/edit prompts from line-by-line lists to comma-separated skill category prompts while leaving highlights and links unchanged.
- `app/resume_evidence/skills_cli.py:63-79` - Switched skills schema editing to comma-separated category prompts with default values.
- `tests/test_resume_evidence_cli.py:68-90` - Added parser tests for internal spaces, optional blank input, and rejected empty comma segments.
- `tests/test_resume_evidence_cli.py:311-528` - Updated project and skills CLI flows for the new prompt model, including blank-input keep behavior and add/drop skill edits.

**Rationale:**
The previous list editing flow forced users to choose between keeping an entire field unchanged or retyping the whole list line by line. Comma-separated prompts make small skill-list edits much lighter while keeping the stored schema unchanged as validated `list[str]` values. Readline prefill improves scalar text edits in the real interactive CLI without changing deterministic test input behavior.

**Tests:**
- `test_comma_skill_parser_preserves_internal_spaces`: validates that skill names such as `Distributed Computing` remain one item.
- `test_comma_skill_parser_allows_empty_input_when_optional`: validates optional blank skill categories still produce an empty list.
- `test_comma_skill_parser_rejects_empty_segments`: validates strict rejection for blank comma segments and trailing commas.
- `test_cli_edit_updates_project_after_apply_and_keeps_id_hidden`: validates project skill add/drop editing and existing hidden IDs.
- `test_skills_cli_edit_keeps_existing_skills_on_blank_input`: validates pressing Enter keeps default category values during edit.
- `test_skills_cli_edit_updates_after_apply`: validates comma-separated skills are persisted after apply.

**Impact:**
Project and standalone skills evidence editing now supports lightweight in-place edits for existing scalar fields and compact comma-separated skill category updates, while preserving deterministic validation and the existing YAML schema.
