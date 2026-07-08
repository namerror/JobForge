### 2026-07-08 - Document resume generation usage

**Agent:** Codex (GPT-5)

**Changes:**
- `README.md:7-9` - Updated the project summary to describe `resume_generation/` as implemented orchestration rather than future-only scaffolding.
- `README.md:65-86` - Refreshed the implemented evidence and generation package descriptions and listed all registered resume evidence schemas.
- `README.md:157-203` - Added a resume-generation usage section covering the run command, generated artifacts, `user/resume_generation/config.yaml`, `user/resume_generation/job_target.yaml`, and every `user/resume_evidence/` schema.
- `README.md:423-427` - Added the resume-generation command to the local run workflow.
- `README.md:446-467` - Removed stale planned/limitations language about missing evidence files and clarified current local orchestration limitations.
- `docs/devlog/Index.md` - Added this session log entry.

**Rationale:**
The README still described resume generation as future work in places even though the repository now has a local pipeline that loads generation config, job target data, and all registered evidence schemas. The updated docs make the current usage path discoverable and identify which user-owned YAML files affect generation.

**Tests:**
- Not run; documentation-only update.

**Impact:**
Users can now find the resume-generation entrypoint, required input files, output artifacts, and the role of each registered evidence schema from the README without reading implementation files first.
