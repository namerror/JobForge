### 2026-03-10 - Embedding testing strategy: unit tests and smoke tests

**Agent:** Claude (Opus 4.6)

**Changes:**
- `tests/test_embeddings.py:464-570` - Added 9 new unit tests covering category independence, deterministic ordering, batching logic, input validation, and subset constraint
- `tests/test_embedding_smoke.py` - New file with 4 live API smoke tests, double-gated behind `--run-smoke` flag and `OPENAI_API_KEY` env var
- `tests/conftest.py:10-32` - Added `--run-smoke` CLI option, `smoke` marker registration, and collection hook to skip/allow smoke tests

**Rationale:**
Step 6 of the development workflow requires tests that validate embedding behavior without depending on actual OpenAI responses. The existing test suite covered basic ordering, cache hits/misses, and dev mode output, but was missing coverage for:
- Category independence (changing one category must not affect another)
- Deterministic ordering across repeated runs
- Batching behavior (embed_skills called once per batch, not per-skill)
- Partial cache scenarios (only uncached skills sent to API)
- Input validation edge cases on the client layer

The smoke tests are intentionally double-gated: users must pass `--run-smoke` AND have `OPENAI_API_KEY` set. This prevents accidental API spend during normal `pytest` runs. The flag-based gate was chosen over just env-var checking because a key might be set in `.env` or the shell profile without the user intending to burn credits on tests.

**Tests:**
- `test_embedding_select_skills_categories_are_independent`: Verifies changing technology input doesn't alter programming/concepts output
- `test_embedding_rank_skills_deterministic_across_runs`: Runs ranking 5 times, asserts identical output each time
- `test_embedding_rank_skills_batches_missing_skills`: Asserts exactly 1 embed_skills call for 4 uncached skills
- `test_embedding_rank_skills_skips_embed_when_all_cached`: No API call when everything is cached
- `test_embedding_rank_skills_partial_cache_only_embeds_missing`: Only uncached skills ("rust", "go") are sent to embed_skills
- `test_embed_skills_rejects_non_string_items`: Validates non-string input rejection
- `test_embed_skills_rejects_empty_string_items`: Validates empty string input rejection
- `test_embed_role_rejects_empty_string`: Validates empty role text rejection
- `test_embedding_select_skills_never_invents_skills`: Output is strict subset of input with top_n=3
- Smoke tests: vector shape, dimension consistency, semantic sanity (PyTorch > Accounting for ML Engineer)

**Impact:**
- CI can now run the full embedding unit test suite without internet or API key (46 unit tests pass, 4 smoke tests skipped)
- Developers can manually verify live API integration with `pytest --run-smoke`
- Batching and caching behavior is now regression-tested, preventing accidental per-skill API calls