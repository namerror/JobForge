### 2026-07-21 - Guard LLM Response Text Extraction Cycles

**Agent:** Codex (GPT-5)

**Changes:**
- `app/skill_selection/llm_client.py:129-170` - Added visited-object tracking to the shared Responses API text extractor so cyclic SDK response parts return `None` instead of recursing indefinitely.
- `resume_generation/__init__.py:7-91` - Made the enrich exports lazy so `python -m resume_generation.enrich` no longer pre-imports the module during package initialization.
- `tests/test_llm_client.py:7-147` - Added direct regression coverage for cyclic response parts while preserving structured-output extraction.
- `tests/test_resume_generation.py:1675-1697` - Added a subprocess smoke test that runs `resume_generation.enrich --help` with warnings promoted to errors.

**Rationale:**
The link-scanning enrichment path uses the shared LLM response text extractor. Some structured Responses API objects can expose nested `content` or `output` references that point back to already-seen objects, so the recursive walker needs a cycle guard before traversing SDK object attributes. The enrich CLI also emitted a `runpy` warning because the package initializer imported `resume_generation.enrich` before module execution; lazy package exports preserve the public import surface without preloading the CLI module.

**Tests:**
- `test_extract_output_text_skips_cyclic_response_parts`: validates cyclic response objects do not raise `RecursionError` and that later structured text is still found.
- `test_enrich_module_help_does_not_emit_runpy_warning`: validates `python -W error -m resume_generation.enrich --help` exits cleanly.
- Focused link-scanning structured-output tests: validate the traceback path still parses structured LLM responses and rejects invalid JSON.

**Impact:**
Link evidence enrichment can fail with a controlled missing-output error instead of crashing on recursive SDK objects, and the enrich module can be run as a CLI without `runpy` warnings.
