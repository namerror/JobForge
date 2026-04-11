### 2026-04-11 - Fix LLM model parameter compatibility

**Agent:** Codex (GPT-5)

**Changes:**
- `app/services/llm_client.py` - Added model-specific Responses API request kwargs construction and omitted `temperature` for `gpt-5`, `gpt-5-mini`, and `gpt-5-nano`.
- `tests/test_llm_client.py` - Added regression coverage proving `gpt-5-mini` requests do not include `temperature`.

**Rationale:**
The LLM skill selector fallback was triggered by an OpenAI 400 response indicating that `temperature` is unsupported for the default `gpt-5-mini` model. Centralizing model-specific request kwargs keeps compatibility rules in one place and avoids scattering conditional parameters through scorer code.

**Tests:**
- `test_score_skills_with_llm_omits_temperature_for_gpt_5_mini`: validates the default model path omits unsupported temperature settings.

**Impact:**
This should allow the default LLM skill-selection model to reach the structured-output request path instead of immediately falling back to baseline because of an unsupported parameter.
