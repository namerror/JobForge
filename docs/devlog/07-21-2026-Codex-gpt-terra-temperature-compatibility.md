### 2026-07-21 - GPT Terra Temperature Compatibility

**Agent:** Codex (GPT-5)

**Changes:**
- `app/skill_selection/llm_client.py:16-21` - Added `gpt-5.6-terra` to the shared Responses API model list that omits `temperature`.
- `tests/test_llm_client.py:88-89` - Added direct helper coverage for the Terra model compatibility rule.
- `tests/test_link_scanning_llm_client.py:364-393` - Added link-scanning coverage proving Terra requests do not send `temperature`.

**Rationale:**
The link-scanning client already uses the shared model compatibility helper before adding `temperature`, but the newer `gpt-5.6-terra` model was not listed as unsupported. Updating the shared helper fixes link scanning and any other stage that uses the same Responses API compatibility path.

**Tests:**
- `test_supports_temperature_returns_false_for_gpt_5_6_terra`: validates the shared helper recognizes Terra as temperature-incompatible.
- `test_scan_evidence_links_with_llm_omits_temperature_for_gpt_5_6_terra`: validates link scanning omits the unsupported parameter for the configured model.
- `PYTHONPATH=. .venv/bin/pytest tests/test_llm_client.py tests/test_link_scanning_llm_client.py -q`: 27 passed.

**Impact:**
Link evidence enrichment can use `gpt-5.6-terra` without failing the OpenAI request on an unsupported `temperature` parameter.
