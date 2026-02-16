# Development Log

This log tracks session-by-session development work, decisions, and changes.

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
