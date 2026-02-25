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
