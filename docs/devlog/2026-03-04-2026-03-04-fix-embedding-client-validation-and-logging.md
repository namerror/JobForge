### 2026-03-04 - Fix embedding client validation and logging

**Changes:**
- `app/services/embedding_client.py:19-109` - Added contextual truncation logging via standard logging extras, propagated optional embedding dimensions to role embeddings, and validated empty skill batches.
- `tests/test_embedding_client.py:1-66` - Added tests for truncation logging, embedding dimension propagation, and empty batch validation.
- `docs/CHANGELOG.md` - Documented embedding client fixes under Unreleased.

**Rationale:**
Standardized truncation telemetry for both roles and skills, ensured consistent embedding dimensionality across role and skill embeddings, and prevented invalid empty batch calls from reaching the API.

**Tests:**
- `test_truncate_texts_logs_truncation_with_context`: validates structured logging extras when truncation occurs.
- `test_embed_role_passes_dimensions`: ensures role embeddings honor `EMBEDDING_DIMENSIONS`.
- `test_embed_skills_empty_list_raises`: guards against empty batch inputs.

**Impact:**
Improves observability, prevents runtime errors in logging and embedding requests, and keeps embedding sizes consistent across scoring inputs.
