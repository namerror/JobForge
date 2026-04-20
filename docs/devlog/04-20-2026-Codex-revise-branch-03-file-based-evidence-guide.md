### 2026-04-20 - Revise Branch 03 as a file-based evidence pipeline guide

**Agent:** Codex (GPT-5)

**Changes:**
- `docs/branch-03-grounded-resume-generation.md` - Reframed the resume-generation branch around user-authored YAML evidence files, deterministic validation, a rebuildable runtime evidence index, synthesis/extraction, and deterministic assembly.
- `docs/branch-03-grounded-resume-generation.md` - Added future path conventions for `data/resume_evidence/` and `app/data/resume_formats/` without defining field-level YAML schemas.
- `docs/branch-03-grounded-resume-generation.md` - Added agent implementation guidance clarifying that schemas should be implemented incrementally with validation, tests, and devlog entries.

**Rationale:**
The previous Branch 03 guide used a generic JSON-style `user_profile.evidence_items` shape, which was too close to a premature schema. The revised guide better reflects the desired local-first, user-friendly design: YAML files are the canonical source of truth, the runtime evidence index is derived and deterministic, synthesis/extraction is the core feature, and assembly remains deterministic. Exact YAML fields are intentionally deferred to implementation passes so future agents can design and test each file format carefully.

**Tests:**
- Documentation-only change; no automated tests were added.
- Verified the existing `Shared Contract` section was preserved.
- Verified the revised guide contains no detailed YAML schema or YAML code block.

**Impact:**
Future Branch 03 work now has clearer boundaries and a more practical architecture for grounded resume generation. Agents can begin with one evidence file at a time, likely `projects.yaml`, without confusing the planning guide for a schema specification.
