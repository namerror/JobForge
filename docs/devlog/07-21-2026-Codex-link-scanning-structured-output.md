### 2026-07-21 - Link Scanning Structured Output

**Agent:** Codex (GPT-5)

**Changes:**
- `app/link_scanning/llm_client.py:14` - Reused the shared Responses API output text extractor.
- `app/link_scanning/llm_client.py:494-496` - Read link-scanning JSON from either top-level `output_text` or nested structured response output.
- `tests/test_link_scanning_llm_client.py:396-445` - Added coverage for a response without top-level `output_text` that still includes valid JSON in nested output content.

**Rationale:**
Some Responses API responses expose generated text through nested output content instead of the top-level `output_text` convenience field. Other LLM clients already handled that shape, but link scanning still required the top-level field and failed before parsing a valid response.

**Tests:**
- `test_scan_evidence_links_with_llm_reads_structured_output_when_output_text_missing`: validates nested output text is accepted and parsed.
- `PYTHONPATH=. .venv/bin/pytest tests/test_link_scanning_llm_client.py -q`: 18 passed.

**Impact:**
Link scanning is more tolerant of Responses API output shapes and no longer fails solely because `output_text` is absent when valid generated JSON is present elsewhere in the response.
