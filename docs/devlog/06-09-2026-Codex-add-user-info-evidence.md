### 2026-06-09 - Add Basic User Info Evidence

**Agent:** Codex (GPT-5)

**Changes:**
- `resume_evidence/models.py` - Added strict `UserInfoFile` validation for required contact fields and optional profile links.
- `resume_evidence/loader.py` - Registered the `user` schema and default `user/resume_evidence/user.yaml` path.
- `resume_generation/main.py` - Validates loaded user evidence as part of the pipeline without changing the returned bullet-point results.
- `user/resume_evidence/user.yaml` - Added placeholder contact evidence for default startup loading.
- `tests/test_resume_evidence.py` and `tests/test_resume_generation.py` - Added user schema coverage and updated generation fixtures to include registered user evidence.
- `README.md` and `docs/agent-context-index.md` - Updated evidence inventory and limitations.

**Rationale:**
The resume generation pipeline needs a grounded source for basic candidate contact info before full resume assembly exists. Keeping the schema in the existing registry preserves deterministic startup loading while avoiding premature CLI editing or output-surface changes.

**Tests:**
- `test_load_user_yaml_returns_typed_runtime_object`: validates `user.yaml` loads into `UserInfoFile`.
- `test_load_user_yaml_rejects_missing_required_field`: ensures required contact fields are enforced.
- `test_load_user_yaml_rejects_extra_top_level_field`: preserves strict schema boundaries.
- `test_load_user_yaml_rejects_unsupported_schema_version`: keeps schema version compatibility explicit.
- `test_load_user_yaml_rejects_empty_required_strings`: rejects blank required contact values.
- `test_load_registered_evidence_loads_registered_schemas`: confirms registered loading includes user, projects, and skills.
- Resume generation pipeline tests now pass loaded user evidence while preserving the existing endpoint call order.

**Impact:**
This gives future resume assembly a validated user-info source while keeping the current selection and bullet-generation pipeline behavior unchanged.
