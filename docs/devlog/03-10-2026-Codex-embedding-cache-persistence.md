### 2026-03-10 - Embedding Cache Persistence Improvements

**Agent:** Codex (GPT-5)

**Changes:**
- `app/services/embedding_cache.py` - Added metadata validation, atomic write-through JSON persistence, and removed `__del__` shutdown writes.
- `app/scoring/embeddings.py` - Added cache store on role miss; added skill cache lookup and store for missing embeddings.
- `tests/test_embeddings.py` - Added write-through and metadata mismatch tests; updated embedding tests to avoid disk writes and validate caching behavior.

**Rationale:**
The previous cache relied on `__del__`, which is unreliable for persistence, and never stored new embeddings. Write-through persistence with atomic file replace prevents data loss and keeps the cache consistent across runs. Metadata validation prevents mixing embeddings across different model configurations.

**Tests:**
- `test_cache_store_persists_role_write_through`: verifies role cache writes include metadata and data.
- `test_cache_store_persists_skill_write_through`: verifies skill cache write-through behavior.
- `test_load_embeddings_cache_rejects_model_mismatch`: ensures mismatched model metadata invalidates the cache.
- `test_embedding_select_skills_stores_role_on_cache_miss`: verifies role embeddings are stored on miss.
- `test_embedding_rank_skills_uses_cache_and_stores_missing`: verifies skill cache hits avoid API calls and misses are persisted.

**Impact:**
Embedding caching is now reliable, persistent, and consistent across runs, reducing API usage and preventing silent cache loss on shutdown.
