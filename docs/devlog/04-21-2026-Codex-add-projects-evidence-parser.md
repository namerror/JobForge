### 2026-04-21 - Add reusable projects evidence parser

**Agent:** Codex (GPT-5)

**Changes:**
- `app/resume_evidence/models.py` - Added strict Pydantic runtime models for `ProjectsFile`, `ProjectRecord`, and `ProjectSkills` with forbidden extra fields, schema version locking, non-empty highlights, duplicate ID validation, and convenience accessors for iteration and ID lookup.
- `app/resume_evidence/loader.py` - Added a reusable YAML loader entrypoint with a schema registry keyed by schema name, startup-oriented default evidence paths under `user/resume_evidence/`, and a bulk loader for registered schemas.
- `app/resume_evidence/__init__.py` - Exported the new parser entrypoint and runtime types for clean imports.
- `app/main.py` - Updated FastAPI lifespan startup to load registered evidence into `app.state.resume_evidence`.
- `user/resume_evidence/projects.yaml` - Added the initial local source-of-truth projects evidence file with schema version `1` and an empty project list so startup loading succeeds by default.
- `tests/test_resume_evidence.py` - Added parser coverage for happy path parsing, missing/extra fields, wrong types, skills shape enforcement, schema version checks, duplicate IDs, unknown schema names, deterministic repeated loads, and startup loading behavior.

**Rationale:**
The first Branch 03 implementation needed a deterministic parser that treats `projects.yaml` as structured source-of-truth data instead of loose dictionaries. I used strict Pydantic models because they fit the repo's existing lightweight dependency set, give clear validation failures, and preserve validated data as typed runtime objects for later pipeline stages. The schema registry keeps the loader reusable for future evidence files without coupling this first pass to `profile.yaml`, `experience.yaml`, or `skills.yaml`.

After the initial parser landed, I also wired in a startup entrypoint so the service loads registered evidence on boot and keeps it on `app.state`. That keeps the first runtime integration simple and matches the intended branch direction of building a runtime evidence index from canonical YAML files. I then moved the evidence root from `data/resume_evidence/` to `user/resume_evidence/` so user-authored resume facts live in a user-scoped directory rather than alongside repository data assets.

Keeping `projects[].id` required aligns the implementation with ADR 003 and gives us stable record-level provenance for future synthesis work. I also added convenience accessors on the validated file model so later stages can iterate projects or build deterministic lookup maps without revalidating or reshaping the parsed data.

**Tests:**
- `test_load_projects_yaml_returns_typed_runtime_object` - Validates successful parsing into typed runtime models and convenience accessors.
- `test_load_projects_yaml_rejects_missing_required_field` - Verifies required project fields are enforced.
- `test_load_projects_yaml_rejects_extra_top_level_field` and `test_load_projects_yaml_rejects_extra_project_field` - Verify unknown fields are rejected.
- `test_load_projects_yaml_rejects_wrong_project_field_types` - Verifies strict type enforcement on project fields.
- `test_load_projects_yaml_rejects_empty_highlights` - Verifies highlights cannot be an empty list.
- `test_load_projects_yaml_rejects_missing_skill_category`, `test_load_projects_yaml_rejects_extra_skill_category`, and `test_load_projects_yaml_rejects_non_list_skill_bucket` - Verify the locked skills taxonomy and bucket types.
- `test_load_projects_yaml_rejects_unsupported_schema_version` - Verifies only schema version `1` is accepted.
- `test_load_projects_yaml_rejects_duplicate_project_ids` - Verifies project IDs must be unique within a file.
- `test_load_evidence_yaml_rejects_unknown_schema_name` - Verifies registry-backed schema lookup fails clearly for unsupported schemas.
- `test_load_projects_yaml_is_deterministic_across_repeated_parses` - Verifies repeat loads produce equivalent runtime objects.
- `test_load_registered_evidence_loads_registered_schemas` - Verifies the startup-oriented bulk loader resolves and parses registered schema files.
- `test_default_evidence_path_points_to_user_directory` - Verifies the default loader path stays rooted under `user/resume_evidence/`.
- `test_app_startup_loads_resume_evidence` - Verifies FastAPI lifespan startup loads evidence into application state.

**Impact:**
This establishes the first reusable evidence-ingestion layer for grounded resume generation and gives the project a concrete, tested entrypoint for `projects.yaml`. The app now eagerly loads registered evidence on startup, which gives later Branch 03 work a stable place to read runtime evidence from while keeping user-authored source-of-truth data under `user/resume_evidence/`.
