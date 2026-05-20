### 2026-05-20 - Add Indexed Highlight Editor

**Agent:** Codex (GPT-5)

**Changes:**
- `app/resume_evidence/projects_cli.py:107-213` - Replaced project-edit highlight replacement with a nested `highlights>` editor that lists temporary indices, supports `edit <index>`, `add`, `delete <index>`, `list`, `help`, and `done`, and prevents deleting the final highlight.
- `tests/test_resume_evidence_cli.py:311-459` - Added CLI coverage for keeping highlights, editing a highlight by temporary index, appending and deleting highlights, rejecting final-highlight deletion, and containing invalid nested commands.
- `docs/decisions/007-modern-cli-selection-ui.md:1-65` - Added a pending ADR outlining feasibility, library options, expected implementation size, and a staged plan for future arrow-key selection.
- `docs/decisions/README.md` - Indexed ADR 007.

**Rationale:**
Highlights are sentence-level evidence and may contain commas, so comma-separated editing would damage valid content. A temporary indexed editor keeps the existing YAML schema and staged update flow while making small highlight edits practical. The pending ADR captures the future richer CLI direction without adding a terminal UI dependency now.

**Tests:**
- `test_cli_edit_updates_project_after_apply_and_keeps_id_hidden`: verifies keeping highlights unchanged still works during project edits.
- `test_cli_edit_updates_highlight_by_temporary_index`: validates indexed highlight edits and comma preservation.
- `test_cli_edit_can_add_and_delete_highlights_by_temporary_index`: validates append and delete behavior in the nested editor.
- `test_cli_edit_rejects_deleting_final_highlight`: validates the non-empty highlights invariant.
- `test_cli_edit_highlight_invalid_commands_do_not_mutate_staged_data`: validates nested command errors stay recoverable.

**Impact:**
Project highlight edits are now much less repetitive while remaining deterministic, staged, and schema-compatible. The modern CLI idea has a documented pending direction for later implementation.
