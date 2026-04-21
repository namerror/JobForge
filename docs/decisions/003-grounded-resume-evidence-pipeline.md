# 003. Grounded Resume Evidence Pipeline

Date: 2026-04-20

## Status

Accepted

## Context

Branch 03 is the first planned expansion beyond skill selection into grounded resume generation. The repo already has a production skill-selection service with deterministic baseline fallback and stable skill-category boundaries, but it does not yet have a resume-generation architecture that defines where user facts live, how support is traced, or how generation avoids inventing claims.

We need a design that keeps resume generation inspectable, file-based, and deterministic at its boundaries. The new design also needs to make room for the existing skill-selection subsystem to plug into the future Skills section without turning skill selection into the whole resume engine.

## Decision

Adopt a file-based grounded resume architecture with these boundaries:

- User-authored YAML files under `data/resume_evidence/` are the canonical source of truth for resume facts.
- A deterministic load/validate/index step builds a runtime evidence index from those files. The index is derived, rebuildable, and does not use LLM or NLP behavior.
- Synthesis/extraction is the first concrete engine contract. It consumes the job target, evidence index, selected skills, and resume format requirements, then returns structured fill data.
- Structured fill data carries record-level provenance refs shaped around `source_file` and `record_id`.
- Deterministic assembly is a separate stage that consumes only structured fill data plus a format definition. Assembly does not select, infer, rewrite, or invent claims.
- Resume format definitions live under `app/data/resume_formats/` as a registry abstraction with one initial default chronological format.
- The first concrete schema pass is intentionally minimal and applies only to `data/resume_evidence/projects.yaml`.

For `projects.yaml`, lock only this root and record shape in the design:

```yaml
schema_version: 1
projects:
  - id: project-id
    name: Project Name
    summary: Short grounded summary
    highlights:
      - Evidence-backed highlight
    active: true
    skills:
      technology: []
      programming: []
      concepts: []
    links: []
```

The required project fields are:
- `id`
- `name`
- `summary`
- `highlights`
- `active`
- `skills`

The optional project field is:
- `links`

Do not lock field-level schemas for `profile.yaml`, `experience.yaml`, or `skills.yaml` in this decision. Keep those files at purpose-and-boundary level only for now.

Treat the existing skill selector as an upstream sub-capability that can later prioritize and fill the resume Skills section, not as the sole source of truth for the broader resume engine.

## Consequences

### Positive
- Keeps user facts in local, inspectable source files instead of hidden generated state.
- Creates a clean architecture boundary between grounded synthesis and deterministic assembly.
- Makes evidence support auditable at the record level for each synthesized item.
- Lets the project start with one concrete schema anchor (`projects.yaml`) without prematurely freezing the entire evidence model.
- Reuses the current skill-category taxonomy and allows the existing skill selector to plug into the resume engine later.

### Negative
- Adds a new multi-stage architecture before any public resume-generation API exists.
- Record-level provenance is easier to work with now, but it is less precise than future field-path or text-span tracing.
- Deferring detailed schemas for `profile.yaml`, `experience.yaml`, and `skills.yaml` means later implementation passes will still need focused design work.

### Neutral
- Generated resumes remain derived artifacts and must not silently mutate evidence files.
- The first documented format is chronological, but the architecture commits to a reusable format registry rather than a single hard-coded template.
- The first synthesis output is structured fill data, not polished prose generation.

## Alternatives Considered

- Design a public resume-generation API first: rejected because the repo does not yet have a stable evidence model or synthesis contract to expose publicly.
- Fully specify all four evidence files now: rejected because it would overfit early assumptions before implementation and validation experience.
- Collapse synthesis and assembly into one generator stage: rejected because it would weaken inspectability and make grounding failures harder to debug.
- Treat skill selection as a required prerequisite for all resume generation: rejected because it is only one prioritization signal and not the whole evidence model.
- Use field-path or text-span provenance immediately: deferred because record-level tracing is sufficient for the first design pass and keeps the contract simpler.
