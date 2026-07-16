### 2026-07-16 - Add Job Focus Generation Stage

**Agent:** Codex (GPT-5)

**Changes:**
- `app/job_focus_generation/models.py:12-85` - Added strict job-focus request, response, and distilled focus schemas.
- `app/job_focus_generation/llm_client.py:28-277` - Added strict JSON-schema LLM client, prompt payload, irrelevant-context exclusions, retry, and token metadata capture.
- `app/main.py:137-157` - Exposed `POST /derive-job-focus` and health config for the new service.
- `resume_generation/job_focus.py:21-84` - Added cached orchestration helper for one job-focus derivation per job target.
- `resume_generation/main.py:87-233` - Inserted job-focus generation between selection and bullet generation and included it in the run manifest.
- `app/bulletpoints_generation/llm_client.py:57-98` - Updated bullet prompts to prefer compact job focus over repeated full job descriptions.
- `docs/CHANGELOG.md:10-24` - Documented the new user-facing job-focus API and pipeline behavior.
- `tests/test_job_focus_generation.py` and `tests/test_resume_generation.py` - Added API, schema, client, cache, manifest, order, and token-usage coverage.

**Rationale:**
Long job descriptions were being sent repeatedly to each bullet-generation call. A cached `job_focus` stage preserves the resume-relevant parts of the JD once, then downstream bullet generation can use the compact distillation while remaining grounded only in supplied project or experience evidence.

**Tests:**
- `test_derive_job_focus_api_success_with_details`: validates the new API response and dev metadata.
- `test_derive_job_focus_with_llm_sends_strict_schema`: validates strict Responses API schema wiring.
- `test_derive_job_focus_posts_job_target_once`: validates orchestration payload and config overrides.
- `test_resume_generation_pipeline_loads_config_job_and_evidence_once`: validates selection -> job focus -> bullets -> assembly ordering and manifest output.
- `test_build_bulletpoint_prompt_payload_prefers_job_focus_over_description`: validates that full JD text is omitted when focus is supplied.

**Impact:**
Resume generation now derives a reusable job context before bullet writing, reducing repeated prompt payload size and making the major pipeline order explicit. Experience selection is still active-record based and remains the main process mismatch with the desired selection-of-experiences flow.
