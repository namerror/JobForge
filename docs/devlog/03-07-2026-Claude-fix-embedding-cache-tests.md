### 2026-03-07 - Fix embedding cache tests after EmbeddingCache refactor

**Agent:** Claude (claude-sonnet-4-6)

**Changes:**
- `tests/test_embeddings.py:7-14` - Removed `cache_lookup` from direct import; added `from app.services.embedding_cache import EmbeddingCache`
- `tests/test_embeddings.py` (cache_lookup section) - Rewrote 5 `test_cache_lookup_*` tests to instantiate `EmbeddingCache` directly via a `_make_cache()` helper and call `cache.cache_lookup()` as a method
- `tests/test_embeddings.py` (embedding_select_skills section) - Replaced all `monkeypatch.setattr(embeddings, "ROLE_EMB_CACHE", {})` with `monkeypatch.setattr(embeddings.cache, "role_cache", {})` across 7 tests
- `README.md` - Added "Running Tests" section documenting `PYTHONPATH=.` requirement, common invocations, and known caveats

**Rationale:**
The `EmbeddingCache` class was extracted into `app/services/embedding_cache.py`, but `tests/test_embeddings.py` was written against the previous design where caching used module-level dicts (`ROLE_EMB_CACHE`, `SKILL_EMB_CACHE`) and a standalone `cache_lookup()` function in `embeddings.py`. After the refactor:
- `cache_lookup` no longer exists as a module-level function — it is a method on `EmbeddingCache`
- `ROLE_EMB_CACHE` / `SKILL_EMB_CACHE` no longer exist as module globals — the live state lives in `embeddings.cache.role_cache` / `embeddings.cache.skill_cache`

This caused a collection-time `ImportError` that blocked all 29 tests from running.

**Tests:**
- `test_cache_lookup_role_hit`: verifies `EmbeddingCache.cache_lookup` returns value on role hit
- `test_cache_lookup_role_miss`: verifies `None` returned when key absent from role cache
- `test_cache_lookup_skill_hit`: verifies `EmbeddingCache.cache_lookup` returns value on skill hit
- `test_cache_lookup_skill_miss`: verifies `None` returned when key absent from skill cache
- `test_cache_lookup_invalid_type_raises`: verifies `ValueError` on unknown cache type
- `test_embedding_select_skills_uses_role_cache`: patching `embeddings.cache.role_cache` now correctly prevents `embed_role` from being called on a cache hit
- `test_embedding_select_skills_calls_embed_role_on_cache_miss`: patching `embeddings.cache.role_cache` to empty dict now correctly triggers `embed_role`

**Impact:**
All 29 embedding tests pass. The `_make_cache()` helper (using `__new__` + direct dict assignment) avoids disk I/O for the `EmbeddingCache` unit tests, keeping them fast and self-contained.
