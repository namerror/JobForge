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
