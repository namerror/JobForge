### 2026-07-15 - Standalone Link Evidence Enrichment

**Agent:** Codex (GPT-5)

**Changes:**
- `resume_generation/main.py` - Removed link scanning from the normal resume generation pipeline.
- `app/link_scanning/models.py` and `app/link_scanning/service.py` - Generalized link scanning from project-only requests to project/experience evidence enrichment requests.
- `app/link_scanning/llm_client.py` - Removed job-target context from scanner prompts, added recruiter-useful technical highlight guidance, and computed scanner output tokens from requested highlight count.
- `resume_generation/enrich.py` - Added standalone evidence enrichment runner and CLI entrypoint that appends non-duplicate scanned highlights to project and experience YAML files.
- `tests/test_link_scanning_llm_client.py`, `tests/test_link_scanning_api.py`, and `tests/test_resume_generation.py` - Updated coverage for the new scanner contract, standalone persistence, dry-run behavior, and pipeline separation.
- `docs/resume-generation-token-efficiency-audit.md` and `docs/CHANGELOG.md` - Documented the implemented standalone enrichment design.

**Rationale:**
Link scanning uses web search and should not be part of every resume drafting run. Moving it into an explicit enrichment flow makes scanned evidence durable, keeps generation cheaper and more deterministic, and lets project and experience records share the same enrichment behavior.

**Tests:**
- `test_scan_evidence_links_with_llm_sends_web_search_request`: validates generic evidence prompts, web search use, and dynamic max output tokens.
- `test_enrich_link_evidence_api_returns_llm_highlight_patch_with_details`: validates the new API response shape and scan metadata.
- `test_run_link_evidence_enrichment_scans_projects_and_experience_and_writes_yaml`: validates project and experience YAML enrichment plus duplicate filtering.
- `test_resume_generation_pipeline_does_not_scan_links_before_bullet_generation`: validates normal resume generation does not call link scanning even when configured.

**Impact:**
Resume generation now consumes already-enriched evidence without web search. Users can run standalone link enrichment when they want to refresh project or experience highlights, with configurable highlight count and token budgeting.
