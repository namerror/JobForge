### 2026-03-04 - Review embedding ranking and rate limit handling

**Changes:**
- `docs/devlog/2026-03-04-review-embedding-scoring-and-rate-limit.md` - Logged review findings only (no code changes).

**Rationale:**
The user requested a review of embedding ranking logic and rate limit handling; documenting findings is required for non-trivial work.

**Tests:**
- None (review-only, no code changes).

**Impact:**
Documents risks around redundant role embeddings per request, lack of retry/backoff on rate limits, and potential silent truncation if embeddings response length mismatches inputs.

**Findings (detail, excluding normalized-skill issue):**
- Redundant role embedding per category: `embedding_select_skills()` calls `embedding_rank_skills()` for each category, and `embedding_rank_skills()` calls `embed_role(role_text)` every time. This makes 3 identical role-embedding calls per request (technology/programming/concepts), increasing cost and rate-limit pressure. Consider embedding the role once per request and reusing the vector. Files: `app/scoring/embeddings.py`.
- Rate-limit handling is not seamless: `openai.RateLimitError` is caught and re-raised as `RuntimeError` with no retry/backoff or fallback. This will fail hard on transient rate limits. Consider adding bounded retry with jitter, or fallback to baseline scoring when embeddings fail. Files: `app/scoring/embeddings.py`, `app/services/embedding_client.py`.
- Potential silent truncation: `zip(skills, skill_vecs)` will silently drop items if `skill_vecs` length is less than `skills` (e.g., partial API response). There is no validation that lengths match. Consider explicit length checks and raising/logging on mismatch. Files: `app/scoring/embeddings.py`, `app/services/embedding_client.py`.
