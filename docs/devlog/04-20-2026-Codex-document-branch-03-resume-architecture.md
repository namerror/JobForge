### 2026-04-20 - Document Branch 03 grounded resume architecture

**Agent:** Codex (GPT-5)

**Changes:**
- `docs/architecture-overview.md` - Added a planned Branch 03 resume-engine section covering the evidence pipeline, shared schema primitives, minimal `projects.yaml` schema, format registry, and structured fill data responsibilities.
- `README.md` - Added a “Planned Grounded Resume Generation” section and clarified that resume generation is planned architecture while the current shipped service remains skill selection only.
- `docs/decisions/003-grounded-resume-evidence-pipeline.md` - Added ADR 003 to lock the file-based evidence pipeline, record-level provenance, minimal `projects.yaml` schema, and separation between synthesis and deterministic assembly.
- `docs/decisions/README.md` - Added ADR 003 to the ADR index.

**Rationale:**
This session needed to turn the Branch 03 planning guide into a concrete architecture baseline without overcommitting the entire evidence schema. I kept the design grounded in user-authored YAML files, made `projects.yaml` the only concrete schema anchor, and documented synthesis and assembly as separate responsibilities so future implementation can stay inspectable and deterministic.

**Tests:**
- Documentation-only change; no automated tests were added.
- Verified the docs still describe `/select-skills` as the only implemented public API today.
- Verified `projects.yaml` is the only evidence file with field-level schema detail in the updated architecture and ADR.
- Verified the documented `projects.yaml` fields are exactly `id`, `name`, `summary`, `highlights`, `active`, `skills`, and optional `links`.

**Impact:**
These docs give Branch 03 a concrete architectural baseline for future implementation work. The repo now has a written decision record for the evidence pipeline, a clearer architecture overview for how the resume engine should fit around existing skill selection, and a README section that explains the new direction without overstating current product scope.
