# 004. User Resume Evidence Root And Projects Milestone

Date: 2026-04-23

## Status

Accepted

## Context

ADR 003 established the grounded resume-evidence pipeline and locked the first concrete `projects.yaml` schema, but it recorded the evidence root as `data/resume_evidence/`. The implemented code and current repo structure now use `user/resume_evidence/` for user-authored source-of-truth data.

Since ADRs are historical records, ADR 003 should remain unchanged. We still need an accepted decision that documents the implemented path correction and the first completed Branch 03 milestone so active docs and future work align with the codebase.

## Decision

Adopt these current-state clarifications for the grounded resume engine:

- The canonical root for user-authored resume evidence is `user/resume_evidence/`.
- The first implemented evidence schema remains `user/resume_evidence/projects.yaml`.
- FastAPI startup loads registered evidence through `load_registered_evidence()` and stores the validated result on `app.state.resume_evidence`.
- Local evidence management for projects uses a staged in-memory session model with explicit `apply` confirmation before writing to disk.
- The current local interface for project evidence management is `python -m app.resume_evidence.cli`.
- ADR 003 remains the architecture baseline for the broader pipeline, while this ADR supersedes its outdated path detail and records the implemented milestone state.

## Consequences

### Positive
- Aligns the ADR record with the implemented `user/`-scoped evidence location.
- Clarifies that `projects.yaml` is no longer only planned; it is implemented and validated at runtime.
- Gives future agents a stable reference for startup loading and CLI-based evidence management.
- Preserves ADR 003 as historical context without rewriting past decisions.

### Negative
- Adds a follow-up ADR to explain a path correction and milestone update instead of keeping all details in one record.
- Future readers need to read ADR 003 and ADR 004 together for the full Branch 03 picture.

### Neutral
- The broader synthesis, format-registry, and deterministic assembly stages remain future work.
- `profile.yaml`, `experience.yaml`, and `skills.yaml` remain planned rather than implemented schemas.
- The FastAPI app title and skill-selection route names remain unchanged in runtime code.

## Alternatives Considered

- Edit ADR 003 directly: rejected because ADRs are intended to remain historical records.
- Ignore the path mismatch and document it only in README/architecture docs: rejected because the canonical evidence root is an architectural concern worth capturing in ADR form.
- Create a brand-new architecture ADR that replaces ADR 003 entirely: rejected because the original pipeline decision is still correct aside from the root-path detail and implemented milestone status.
