### 2026-06-23 - Add experience bullet generation

**Agent:** Codex (GPT-5)

**Changes:**
- `app/bulletpoints_generation/models.py:49-75` - Generalized bullet generation requests to accept exactly one project or experience evidence record.
- `app/bulletpoints_generation/llm_client.py:48-148` - Added project/experience prompt payload handling and evidence-specific instruction wording.
- `app/bulletpoints_generation/service.py:56-122` - Forwarded experience evidence through the existing LLM generation service and logged generic evidence metadata.
- `resume_generation/bullet_points.py:60-101` - Added active-experience bullet generation over the existing `/generate-bulletpoints` endpoint with a separate cache stage.
- `resume_generation/main.py:98-122` and `resume_generation/assembly.py:25-75` - Ran experience bullet generation in the pipeline and assembled generated experience bullets into the intermediate resume result.
- `resume_generation/models.py:257-260` - Added `ExperienceBulletPointResult` for generated experience bullet payloads.
- `tests/test_bulletpoints_generation_models.py`, `tests/test_bulletpoints_generation_api.py`, `tests/test_bulletpoints_llm_client.py`, and `tests/test_resume_generation.py` - Added coverage for experience request validation, prompt payloads, orchestration, caching, and assembly.

**Rationale:**
Experience evidence has the same grounded summary/highlights/skills shape as project evidence, so reusing the existing bullet generation subsystem avoids a duplicate LLM path. The request model now preserves honest typing for both evidence types while preventing ambiguous requests, and the resume pipeline keeps project link scanning/selection separate from experience generation as intended.

**Tests:**
- `test_bullet_generation_request_accepts_full_experience_record`: validates typed experience request parsing.
- `test_bullet_generation_request_requires_exactly_one_evidence_record`: validates project/experience ambiguity rejection.
- `test_generate_bulletpoints_api_accepts_experience_record`: validates the API forwards experience records to the bullet generator.
- `test_build_bulletpoint_prompt_payload_supports_experience_evidence`: validates experience prompt grounding fields and link exclusion.
- `test_generate_experience_bullet_points_posts_once_per_active_experience`: validates pipeline adapter behavior and inactive experience skipping.
- `test_resume_generation_pipeline_loads_config_job_and_evidence_once`: validates full orchestration now passes generated experience bullets into assembly.
- `PYTHONPATH=. pytest tests/test_bulletpoints_generation_models.py tests/test_bulletpoints_generation_api.py tests/test_bulletpoints_llm_client.py tests/test_resume_generation.py`: 55 passed.

**Impact:**
The resume generation pipeline now tailors active work experience bullets to the target job using the same grounded generation path already used for projects, without adding experience selection or link scanning.
