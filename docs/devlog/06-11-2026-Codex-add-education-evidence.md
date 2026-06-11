### 2026-06-11 - Add Education Evidence

**Agent:** Codex (GPT-5)

**Changes:**
- `resume_evidence/models.py` - Added strict education evidence models for schools, degrees, dates, location, grade, and relevant coursework.
- `resume_evidence/loader.py` - Registered the `education` schema and default `user/resume_evidence/education.yaml` path.
- `resume_evidence/__init__.py` - Exported education evidence model types.
- `resume_generation/main.py` - Validates loaded education evidence before running selection and bullet generation.
- `user/resume_evidence/education.yaml` - Added an example education record for default startup loading.
- `tests/test_resume_evidence.py` and `tests/test_resume_generation.py` - Added education loading, validation, registry, startup, and pipeline checks.

**Rationale:**
Education needs to become a first-class resume evidence layer without changing the current generation output surface. Registering it alongside the existing evidence schemas keeps startup and pipeline loading deterministic while preserving the current selection and bullet-point orchestration behavior.

**Tests:**
- `test_load_education_yaml_returns_typed_runtime_object`: validates typed education parsing.
- `test_load_education_yaml_rejects_missing_required_field`: enforces required education fields.
- `test_load_education_yaml_accepts_missing_optional_end`: confirms `end` remains optional.
- `test_load_education_yaml_rejects_extra_top_level_field` and `test_load_education_yaml_rejects_extra_record_field`: preserve strict schema boundaries.
- `test_load_registered_evidence_loads_registered_schemas`: confirms registry loading includes education.
- `test_resume_generation_pipeline_requires_loaded_education` and `test_resume_generation_pipeline_rejects_invalid_loaded_education`: ensure pipeline validation fails before orchestration when education evidence is absent or invalid.
- `.venv/bin/python -m pytest tests/test_resume_evidence.py tests/test_resume_generation.py`: 61 passed.

**Impact:**
The resume generation pipeline now has a validated education evidence source ready for future resume assembly while existing generated bullet-point behavior remains unchanged.
