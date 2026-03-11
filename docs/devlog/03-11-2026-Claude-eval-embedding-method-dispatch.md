### 2026-03-11 - Add embedding method support to eval script

**Agent:** Claude (Opus 4.6)

**Changes:**
- `scripts/eval.py:19` - Import `embedding_select_skills` from `app.scoring.embeddings`
- `scripts/eval.py:84-113` - New `select_skills()` dispatcher that reads `settings.METHOD` and routes to `baseline_select_skills` or `embedding_select_skills`
- `scripts/eval.py:116-151` - Updated `evaluate()` to use the dispatcher, extract `job_text` from eval cases, and include `"method"` in output
- `scripts/eval.py:204,220` - Print active method name in CLI output
- `scripts/eval.py:1-12` - Updated module docstring with METHOD usage examples

**Rationale:**
The eval script was hardcoded to only use `baseline_select_skills`. With the embedding scorer implemented, we need the eval harness to support both methods so we can compare their performance on the same eval cases. Rather than adding a CLI flag for method selection, the script reads `settings.METHOD` (from `.env` or env var) to stay consistent with how the rest of the app resolves the scoring method. A `select_skills()` dispatcher centralizes the branching logic and passes the appropriate parameters to each scorer (e.g. `include_zero` for baseline, `job_text` for embeddings).

**Tests:**
- Verified baseline path works: `METHOD=baseline python scripts/eval.py` runs successfully
- Verified unknown method raises a clear `ValueError`

**Impact:**
- Enables side-by-side evaluation of baseline vs embedding scorers using the same eval cases and metrics
- `job_text` is now extracted from eval case inputs, allowing embedding-based scoring to leverage job descriptions when available
- Output JSON now includes `"method"` field for traceability