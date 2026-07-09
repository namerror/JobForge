### 2026-07-09 - Fix Resume Generation Agentic Issues

**Agent:** Codex (GPT-5)

**Changes:**
- `app/bulletpoints_generation/llm_client.py:158-174` - Added aggregated attempt metadata for bullet-generation retries.
- `app/bulletpoints_generation/llm_client.py:267-346` - Added one retry for missing or malformed bullet LLM output, with retry reason and per-attempt token metadata.
- `app/skill_selection/llm_client.py:93-132` - Added structured Responses API output extraction when `output_text` is absent.
- `resume_generation/main.py:37-112` - Added the default run-manifest path plus manifest build/write helpers.
- `resume_generation/main.py:141-333` and `resume_generation/selection.py:107-175` - Collected stage response metadata and wrote `resume_run_manifest.json` without changing `resume_result.json`.
- `app/config.py:37`, `user/resume_generation/config.yaml:4-32`, and `app/skill_selection/data/role_profiles/backend.yaml:1-36` - Increased bullet token defaults, raised the user pipeline timeout, limited project selection to two projects, and expanded backend profile keywords.
- `.gitignore:11` - Ignored the new generated run-manifest artifact.
- `tests/test_bulletpoints_llm_client.py`, `tests/test_llm_client.py`, `tests/test_resume_generation.py`, `tests/test_baseline.py`, `tests/test_config.py`, and `tests/test_health.py` - Added and updated regression coverage for the fixes.

**Rationale:**
The agentic test report showed that the pipeline could complete only after manual token and timeout tuning, and that the final resume artifact hid important fallback details. The changes keep the existing intermediate resume schema stable while adding a companion manifest for audit metadata. Bullet generation now retries the reported malformed JSON path once with a larger output budget, and skill selection can parse structured Responses API output before falling back.

**Tests:**
- `test_generate_bulletpoints_with_llm_retries_malformed_json`: validates retry behavior, larger retry budget, and aggregated attempt token metadata.
- `test_score_skills_with_llm_reads_structured_output_when_output_text_missing`: validates skill LLM parsing when `output_text` is absent.
- `test_resume_generation_pipeline_loads_config_job_and_evidence_once`: validates `resume_result.json` remains section-only and the companion manifest records fallback, stage, and token metadata.
- `test_baseline_select_skills_backend_api_target_prioritizes_specific_terms`: validates backend/API fallback ranking keeps target-specific skills ahead of distractors.
- `PYTHONPATH=. .venv/bin/python -m pytest`: 452 passed, 4 skipped.

**Impact:**
Resume generation is less brittle under current `gpt-5-mini` bullet workloads, default user runs use more realistic timeout/token settings, weak-fit project inclusion is reduced, and future debugging can inspect selection fallback and stage/cache metadata from the manifest artifact.
