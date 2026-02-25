### 2026-02-24 - Migrate role profiles from Python dict to YAML files

**Changes:**
- `app/data/role_profiles/general.yaml` - Created (extracted from ROLE_PROFILES dict)
- `app/data/role_profiles/backend.yaml` - Created
- `app/data/role_profiles/frontend.yaml` - Created
- `app/data/role_profiles/fullstack.yaml` - Created
- `app/data/role_profiles/data.yaml` - Created
- `app/data/role_profiles/devops.yaml` - Created
- `app/data/role_profiles/security.yaml` - Created
- `app/data/role_profiles/mobile.yaml` - Created
- `app/data/role_profiles/ml_ai.yaml` - Created (key `ml/ai`; `/` not valid in filenames)
- `app/scoring/role_profiles.py:1-24` - Replaced hardcoded dict with `_load_role_profiles()` loader using PyYAML
- `requirements.txt` - Regenerated via `pip freeze`; added `PyYAML==6.0.3`

**Rationale:**
Role profile data was hardcoded in Python, making it harder to read and edit without touching source code. Moving to individual YAML files per role separates data from logic, keeps files small, and aligns with the CLAUDE.md guideline to store config data in `app/data/`. The `ROLE_PROFILES` dict and `detect_role_family` exports are unchanged, so no consumers needed modification. `ml_ai.yaml` maps to the `"ml/ai"` key via a `_FILENAME_TO_KEY` lookup to handle the filename constraint.

**Tests:**
No new tests added — existing 83 tests validate the loaded data produces identical behavior to the hardcoded dict (all pass).

**Impact:**
Role profiles can now be edited as plain YAML without touching Python code. Adding a new role only requires dropping a new YAML file in `app/data/role_profiles/`.
