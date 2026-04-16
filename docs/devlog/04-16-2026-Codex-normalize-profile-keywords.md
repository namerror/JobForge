### 2026-04-16 - Normalize Profile Keywords During Baseline Matching

**Agent:** Codex (GPT-5)

**Changes:**
- `app/scoring/baseline.py:13-30` - Added normalized role profile keyword collection and updated baseline scoring to compare normalized input skills against normalized profile keywords.
- `tests/test_baseline.py:64-177` - Added regression tests for backend aliases (`AWS`, `Node.JS`), general profile aliases (`GCP`, `OOP`), and the intentional non-change for one-way partial matching.
- `tests/test_baseline_filter.py:117-154` - Added baseline-filter coverage proving normalized profile aliases stay in the baseline pass and only unrecognized skills reach the second-pass scorer.
- `docs/architecture-overview.md:98-101` - Documented that role profile keywords are canonicalized before baseline matching.

**Rationale:**
The baseline scorer normalized incoming skills but compared them against raw YAML keywords. Profile entries such as `aws`, `node.js`, `gcp`, and `oop` were therefore missed after the incoming skill canonicalized to values such as `amazon web services`, `nodejs`, `google cloud platform`, or `object-oriented programming`. Normalizing profile keywords at runtime preserves the readable, flexible YAML data while keeping the comparison deterministic.

**Tests:**
- `test_score_skill_exact_match_normalizes_backend_profile_keywords`: validates `AWS` and `Node.JS` now score as exact backend technology matches.
- `test_score_skill_exact_match_normalizes_general_profile_keywords`: validates alias-backed keyword normalization outside the backend profile.
- `test_score_skill_does_not_bidirectionally_partial_match_profile_keyword`: confirms this change does not fix or broaden partial matching for `Database Management`.
- `test_baseline_filter_keeps_normalized_profile_aliases_in_baseline`: validates alias-backed backend matches are not sent to embeddings/LLM second-pass scoring.
- `PYTHONPATH=. .venv/bin/pytest tests/test_baseline.py tests/test_baseline_filter.py -q`: 69 passed.
- `PYTHONPATH=. .venv/bin/pytest -q`: 164 passed, 4 skipped.

**Impact:**
Known skills stored in role profiles through synonyms now remain in the deterministic baseline path, reducing unnecessary model-backed scoring while preserving existing category boundaries and one-way partial matching behavior.
