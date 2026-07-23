### 2026-07-23 - Resume Generation Frontend Integration

**Agent:** Codex (GPT-5)

**Changes:**
- `app/resume_generation/api.py:31` - Added targeted `evidence_id` support to the resume-generation link enrichment facade.
- `app/resume_generation/api.py:91` - Added request-scoped job target overrides to the `.tex` generation request.
- `app/resume_generation/enrich.py:235` - Added persisted single-record link enrichment filtering for project and experience evidence.
- `app/resume_generation/main.py:130` - Added request-time job target override plumbing and manifest source metadata.
- `frontend/src/App.tsx:335` - Added `.tex`, PDF, and per-record enrichment action handlers with saved-state gating.
- `frontend/src/App.tsx:791` - Added the Resume generation panel and per-item link scanning controls for projects and experience.
- `frontend/src/api.ts:45` - Added typed frontend client methods for resume `.tex`, PDF, and link enrichment calls.
- `frontend/src/types.ts:108` - Added frontend types for resume generation and enrichment payloads/responses.
- `docs/CHANGELOG.md:11` - Documented the user-facing generation and enrichment controls.

**Rationale:**
The existing backend already owned synchronous resume-generation endpoints, but the Vite workbench had no way to call them. The implementation keeps job targets request-scoped so frontend input overrides backend defaults without mutating `user/resume_generation/job_target.yaml`. Targeted enrichment reuses the existing atomic YAML enrichment flow instead of making the lower-level scan endpoint responsible for persistence.

**Tests:**
- `test_run_link_evidence_enrichment_scans_only_target_record`: validates persisted enrichment can target one project record.
- `test_resume_generation_tex_route_accepts_job_target_override`: validates the facade accepts frontend job target input.
- `test_resume_generation_pipeline_job_target_override_reaches_stage_services`: validates overridden job title and description reach selection, focus, and bullet stages.
- Frontend API tests validate `.tex`, PDF blob, and targeted enrichment client calls.
- Frontend App tests validate dirty-state blocking, PDF prerequisite messaging, and project/experience per-item enrichment calls.
- Ran `PYTHONPATH=. pytest tests/test_resume_generation.py tests/test_link_scanning_api.py`.
- Ran `npm test` in `frontend/`.

**Impact:**
The workbench can now generate resume artifacts from user-provided job targets, expose PDF rendering, and selectively enrich individual project or experience evidence records through link scanning while preserving the staged-edit workflow.
