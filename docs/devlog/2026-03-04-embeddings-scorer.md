### 2026-03-04 - Implement embeddings scorer

**Changes:**
- `app/scoring/embeddings.py` - Added `cosine_similarity()`, `embedding_rank_skills()`, and `embedding_select_skills()` on top of existing utility functions

**Rationale:**
Implemented the per-category embedding scorer that mirrors the `baseline_select_skills()` interface. Uses the existing `embed_role`/`embed_skills` client wrapper and `construct_role_text` utility already in the file. numpy is used for cosine similarity. Rate limit errors from the OpenAI API are caught, logged, and re-raised as `RuntimeError` with a clear message. Dev mode surfaces per-skill similarity scores and a `_warnings` list (e.g., when role text is suspiciously short).

**Tests:**
- Not added in this session — tests for `embedding_select_skills` and `embedding_rank_skills` (with mocked `embed_role`/`embed_skills`) are the next step

**Impact:**
The scorer is now ready to be wired into `app/services/skill_selector.py` under `method="embeddings"`. No other files were changed.
