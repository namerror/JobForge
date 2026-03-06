### 2026-03-06 - Fix embeddings stale kwarg bug and add unit tests

**Changes:**
- `app/scoring/embeddings.py:167-174` - Removed stale `role_text=role_text` kwarg from `embedding_rank_skills` call inside `embedding_select_skills`. This was a guaranteed `TypeError` at runtime since `embedding_rank_skills` has no such parameter.
- `tests/test_embeddings.py` - Created new test file with 29 unit tests covering all public functions in `embeddings.py`.

**Rationale:**
The embedding scorer was written but untested. A leftover `role_text=role_text` kwarg (likely from an earlier signature that was later refactored) would have caused every call to `embedding_select_skills` to crash with a `TypeError`. Tests were needed to catch regressions like this and to validate caching, ranking, and error-handling paths without hitting the real OpenAI API.

**Tests:**
- `test_normalize_skill_*` (3): strip/lowercase, synonym lookup, unknown passthrough
- `test_construct_role_text_*` (3): with job_text, without job_text, empty job_text
- `test_cosine_similarity_*` (4): identical vectors, orthogonal, opposite, zero vector
- `test_cache_lookup_*` (5): role hit, role miss, skill hit, skill miss, invalid type raises
- `test_embedding_rank_skills_*` (7): empty list, empty dev_mode, ordering by similarity, top_n slicing, dev_mode details structure, length mismatch raises, stable tiebreak by normalized name
- `test_embedding_select_skills_*` (7): role cache hit skips API, cache miss calls API once, output is subset of input, short role text triggers warning log, dev_mode surfaces warnings in details, rate limit → RuntimeError, empty categories return empty lists

**Known gaps (not fixed here):**
- `SKILL_EMB_CACHE` is loaded but never consulted — skills always hit the API.
- Neither role nor skill embeddings fetched from the API are written back to cache.

**Impact:**
Unblocks safe iteration on the embedding scorer. The `TypeError` bug would have prevented any production use of `embedding_select_skills`.
