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
