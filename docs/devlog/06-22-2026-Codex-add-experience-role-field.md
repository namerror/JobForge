### 2026-06-22 - Add experience role field

**Agent:** Codex (GPT-5)

**Changes:**
- `resume_evidence/models.py:56-67` - Added required `role` to strict experience evidence records.
- `resume_evidence/session.py:459-535` - Threaded `role` through staged experience create/edit operations while preserving stable generated ids.
- `resume_evidence/cli/experience.py:81-135` - Added role display and create/edit prompts to the experience CLI.
- `resume_generation/models.py:276-283` and `resume_generation/assembly.py:58-66` - Added `role` to intermediate resume experience output and populated it from evidence.
- `user/resume_evidence/experience.yaml` - Updated the starter experience record with a role value.
- `tests/test_resume_evidence.py`, `tests/test_resume_evidence_cli.py`, and `tests/test_resume_generation.py` - Updated fixtures and assertions for required role validation, session editing, CLI output, and resume assembly.

**Rationale:**
`id` is an internal stable key generated from the initial company/name and preserved across edits, so it should not stand in for a user-facing job title. A distinct `role` field keeps evidence semantics clear and lets resume output render company and title separately.

**Tests:**
- `test_load_experience_yaml_returns_typed_runtime_object`: validates role parsing on typed experience evidence.
- `test_load_experience_yaml_rejects_missing_required_field`: now verifies missing `role` is rejected.
- `test_experience_session_create_stages_changes_without_writing_file` and `test_experience_session_update_keeps_original_id_on_rename`: validate role persistence and id stability.
- `test_experience_cli_list_and_show` and `test_experience_cli_create_edit_delete_and_apply`: validate CLI role display and prompts.
- `test_assemble_intermediate_resume_result_builds_deterministic_schema`: validates role propagation into resume output.
- `.venv/bin/python -m pytest tests/test_resume_evidence.py tests/test_resume_evidence_cli.py tests/test_resume_generation.py`: 171 passed.

**Impact:**
Experience evidence now records the actual role/title separately from the stable id and company/name, and generated intermediate resume JSON can expose that role for downstream rendering.
