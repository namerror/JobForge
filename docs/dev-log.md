# Development Log

This log tracks session-by-session development work, decisions, and changes.

---

### 2026-02-25 - Add agent architecture overview and instruction index

**Changes:**
- `docs/architecture-overview.md` - Added module dependency map, request flow diagram, scoring flow, and extension points for `app/`
- `docs/agent-context-index.md` - Added centralized index for agent instructions and recommended read order
- `AGENTS.md` - Added pointers to the new agent context index and architecture overview
- `CLAUDE.md` - Added pointers to the new agent context index and architecture overview

**Rationale:**
Agents needed a fast, explicit way to understand module relationships and runtime logic flow without repeating or fragmenting instruction context. A dedicated architecture document keeps flow knowledge separate from policy docs, while a single index file improves discoverability and onboarding speed.

**Tests:**
- No automated tests added or run (documentation-only changes).

**Impact:**
Reduces time-to-context for future agent sessions, makes dependency and control flow easier to trace, and keeps instruction files linked through one canonical navigation entry point.

---

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

---

### 2026-02-17 - Implement eval_case scoring function

**Changes:**
- `scripts/eval.py:1-46` - Implemented `eval_case()`, added `settings` import and `CATEGORIES` constant

**Rationale:**
The evaluation harness needed a concrete scoring function to quantify how well the baseline selector matches human-curated expected outputs. Jaccard similarity was chosen because it naturally accounts for both directions of error — missing expected items and returning unexpected ones — without requiring a separate precision/recall decomposition. Each category is scored independently, then averaged to produce a single per-case score.

**Scoring logic:**
- Expected list is trimmed to `settings.TOP_N` elements before comparison (order in expected file determines priority)
- Per-category score = `|hits| / (|hits| + |missing| + |unexpected|)` (Jaccard index, 0–1)
- Edge case: both sets empty → score `1.0`
- `average_score` = mean of the three category scores

**Return shape:**
```python
{
    "scores": {"technology": 0.8, "programming": 1.0, "concepts": 0.6667},
    "average_score": 0.8222,
    "mistakes": {
        "technology": {"missing": ["React"], "unexpected": ["Vue"]},
        ...
    }
}
```

**Impact:**
Evaluation harness (`scripts/eval.py`) is now fully runnable end-to-end. Results surface per-category accuracy and exact mistake lists, enabling targeted improvement of role profiles and synonyms.

---

### 2026-02-17 - Expand eval cases to 20 realistic user inputs

**Changes:**
- `data/eval_cases.json` - Grew from 2 to 20 eval cases covering 18 additional job roles

**Rationale:**
The goal is to stress-test the baseline skill selector with realistic, messy user inputs rather than hand-crafted passing cases. Each case simulates a real user filling in their resume skills without knowledge of the system's internals. Key variation patterns:

- **Role variety**: Frontend, Full-Stack, Back-End, DevOps, ML Engineer, Data Analyst, Cloud Architect, Cyber Security, iOS, Android, QA, Embedded, Data Engineer, SRE, Blockchain, Game Dev, AI Research, Junior Dev — covering most role families plus several (QA, Game Dev, Blockchain, Embedded) that fall through to "general"
- **Synonym/formatting noise**: `ReactJS`, `VueJS`, `Node JS`, `NodeJS`, `Tailwind CSS`, `React.js`, `Pytorch`, `Scikit-Learn`, `sklearn`, `React-Native`, `Amazon Web Services`, `Microsoft Azure`, `Google Cloud`, `Amazon Cloud`, `Google Cloud Platform`, `Apache Spark`
- **Cross-role contamination**: Every case includes a handful of skills irrelevant to the role (e.g. `React` for a backend engineer, `Machine Learning` for a QA engineer, `Docker` for an iOS developer)
- **Untracked tools**: `Figma`, `JIRA`, `Tableau`, `Power BI`, `Looker`, `Excel`, `Xcode`, `CocoaPods`, `TestFlight`, `Airflow`, `Snowflake`, `dbt`, `PagerDuty`, `Solidity`, `Unity`, `HuggingFace`, `CUDA`, `MATLAB`, `VBA`, `Blender` — tools real users list that our profiles don't know about
- **Filler/soft skills in concepts**: `Communication`, `Teamwork`, `Problem Solving`, `Version Control`, `Research Methodology` — padding users copy from generic resume templates
- **Case/casing variation in job_role**: `devops engineer`, `android developer`, `game developer`, `site reliability engineer` (all lowercase), `Back-End Engineer` (hyphen), `QA / Test Engineer` (slash)

**Tests:**
No automated tests added — these are evaluation-only data fixtures consumed by `scripts/eval.py`.

**Impact:**
Provides a diverse, realistic test bed for measuring Precision@N and category hit-rate of the baseline scorer across a wide range of role families, synonym forms, and noise patterns.

*2026-02-17 (amendment)* — Expanded each case with additional irrelevant skills to simulate a user dumping their full skill inventory. Every case now includes 5–10 skills that are clearly off-domain for the role (e.g. Unity/Unreal Engine for a Data Engineer, TensorFlow for a QA Engineer, FreeRTOS/STM32 for a Frontend Engineer, Excel/Tableau for a DevOps engineer, Assembly/MATLAB across most roles). This reflects the real usage pattern: a user feeds all their skills regardless of relevance, and the service must rank and filter for the target job role.

---

### 2026-02-16 - Add comprehensive tests for baseline_select_skills() function

**Changes:**
- `tests/test_baseline.py` - Added 17 new tests for `baseline_select_skills()` function (total now 53 tests)
- `app/scoring/baseline.py:55` - Fixed bug: changed `skills.role` to `skills.job_role` to match model attribute
- `app/scoring/baseline.py:55` - Updated return type annotation from `tuple[list[str], dict | None]` to `tuple[dict, dict | None]`

**Rationale:**
The `baseline_select_skills()` function is the main entry point for the scoring system, orchestrating role detection and skill ranking across all three categories (technology, programming, concepts). Comprehensive testing ensures:
1. **Determinism**: Same skills in different order produce identical rankings (critical for consistent user experience)
2. **Role detection**: Various job title formats ("Backend Engineer", "SWE Intern", "Full-Stack Developer") correctly map to role families
3. **No skill invention**: Output is always a subset of input (core requirement)
4. **Cross-category consistency**: All three categories are processed correctly

**Tests Added (17 total):**
- **Determinism (2 tests)**: Different input order, multiple runs produce identical results
- **Role detection (8 tests)**: Backend Engineer, SWE Intern, Software Engineer, Full Stack Developer, DevOps Engineer, ML Engineer, role with hyphens, case-insensitive matching
- **Contract validation (4 tests)**: All categories processed, never invents skills, preserves casing, respects TOP_N limit
- **Edge cases (3 tests)**: Empty categories, all empty, cross-category consistency

**Bug Fixed:**
- Line 57 was accessing `skills.role` but `SkillSelectRequest` model uses `job_role` attribute, causing AttributeError

**Impact:**
- Test coverage increased from 49 to 66 tests (all passing)
- `baseline_select_skills()` is now fully tested and production-ready
- Validates end-to-end flow: job role → role family detection → skill ranking → structured output
- Ensures deterministic behavior critical for user trust and evaluation metrics

---

### 2026-02-16 - Complete test suite for baseline scoring

**Changes:**
- `tests/test_baseline.py` - Expanded from 3 to 36 tests covering normalization, scoring, and ranking
- `tests/test_health.py` - Expanded from 1 to 13 integration tests for API endpoints
- `tests/conftest.py` - Created pytest config to enable DEV_MODE for tests
- `app/scoring/baseline.py:6` - Fixed TOP_N type conversion (string → int)
- `app/scoring/baseline.py:30-34` - Added empty string handling to prevent false partial matches

**Rationale:**
Tests ensure deterministic behavior, proper tie-breaking, and guarantee output is always a subset of input (no invented skills). Comprehensive coverage prevents regressions as scoring logic evolves. Empty string handling prevents false positives where empty strings would match any keyword due to Python's substring matching behavior.

**Tests Added:**
- **Normalization (4 tests)**: casing, whitespace trimming, synonym mapping, unknown skill preservation
- **Scoring (19 tests)**: exact/partial matches, role inheritance, fallback to general profile, edge cases (empty/whitespace), determinism verification, all role types (backend, frontend, fullstack, devops, ml/ai, security, mobile, data)
- **Ranking (13 tests)**:
  - Determinism: same input produces identical output across runs
  - Tie-breaking: alphabetical sorting when scores equal
  - Duplicate stability: consistent scores for duplicate skills
  - Never invents skills: output always subset of input (including with synonyms)
  - Additional: empty lists, single skills, casing preservation, TOP_N limits, stable sorting

**Impact:**
- All 49 tests pass successfully
- Baseline scorer is fully tested and ready for API integration
- Test infrastructure (conftest.py) supports DEV_MODE for detailed debugging
- Validates core requirement: never invent skills, only select from input
