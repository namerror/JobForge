### 2026-03-15 - Fix OpenAI Client Init in embed_role

**Agent:** Codex (GPT-5)

**Changes:**
- `app/services/embedding_client.py:66` - Use keyword argument `api_key` when instantiating `OpenAI` client in `embed_role`.
- `tests/test_embedding_client.py:47` - Allow dummy OpenAI client to accept keyword args to mirror real client signature.

**Rationale:**
The OpenAI Python client in `openai==2.24.0` expects keyword arguments for initialization. The previous positional call in `embed_role` would raise a `TypeError`, blocking embeddings in runtime. The test stub needed to accept keyword args to stay aligned with the real client API.

**Tests:**
- `test_embed_role_passes_dimensions`: still validates dimension propagation and now works with keyword initialization.

**Impact:**
Embeddings for role text now initialize the OpenAI client correctly, preventing runtime failures while keeping tests aligned with the client signature.
