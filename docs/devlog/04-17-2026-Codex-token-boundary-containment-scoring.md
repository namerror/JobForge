### 2026-04-17 - Token-Boundary Containment Scoring

**Agent:** Codex (GPT-5)

**Changes:**
- `app/scoring/baseline.py:3-83` - Added normalized token-boundary phrase helpers and updated baseline scoring so exact matches or full phrase containment in either direction score `3.0`, while the existing weaker one-way partial match remains `1.0`.
- `tests/test_baseline.py:168-273` - Replaced the old one-way containment expectation and added regression coverage for `Database Management`, issue #3 REST API phrase variants, bidirectional containment, and raw-substring false positives.
- `tests/test_baseline_filter.py:156-190` - Added baseline-filter coverage proving token-containment matches stay in the deterministic baseline pass and are not sent to the model-backed second pass.
- `docs/architecture-overview.md:103-107` - Documented the updated score assignment rules.

**Rationale:**
The baseline scorer already normalized incoming skills and profile keywords, but partial matching only recognized the input phrase when it appeared inside a profile keyword. That missed user-provided phrases like `Database Management` for a backend `database` concept and issue #3 variants such as `RESTful APIs Design`.

Token-boundary containment gives these deterministic profile matches full baseline credit without raw substring false positives such as `JavaScript` matching `java`, `cloudformation` matching `cloud`, or generic short keywords matching inside unrelated words. Token-level synonym expansion keeps known aliases such as `apis` aligned with canonical forms without adding fuzzy typo correction.

**Tests:**
- `test_score_skill_token_boundary_containment_profile_keyword_inside_skill`: validates `Database Management` now scores as a strong backend concept match.
- `test_score_skill_token_boundary_containment_skill_inside_profile_keyword`: validates bidirectional phrase containment when the candidate is shorter than the profile keyword.
- `test_score_skill_token_boundary_containment_normalizes_issue_three_phrase_variants`: validates REST API phrase variants from issue #3.
- `test_score_skill_token_boundary_containment_avoids_raw_substring_false_positives`: guards against unsafe substring matches.
- `test_score_skill_token_boundary_containment_allows_short_keywords_as_standalone_tokens`: confirms short keywords still match as full tokens.
- `test_baseline_filter_keeps_token_containment_matches_in_baseline`: validates baseline-filter routing for newly recognized phrase-containment matches.
- `PYTHONPATH=. .venv/bin/pytest tests/test_baseline.py tests/test_baseline_filter.py -q`: 74 passed.
- `PYTHONPATH=. .venv/bin/pytest -q`: 169 passed, 4 skipped.
- `METHOD=baseline PYTHONPATH=. .venv/bin/python scripts/eval.py -f eval_cases_basic.json`: exited 0 with overall score `0.8506`.

**Impact:**
The deterministic baseline now recognizes fuller user skill phrases without sending them to embeddings or LLM scoring, improving baseline-filter efficiency while preserving category boundaries, stable ordering, and the existing public API.
