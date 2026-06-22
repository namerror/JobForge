# Branch 03: Grounded Resume Generation

## Purpose

Branch 03 is no longer only a forward-looking design space. The repo now includes the first implemented milestone of the grounded resume pipeline:

- strict `projects.yaml` parsing
- strict `skills.yaml` parsing
- startup loading into `app.state.resume_evidence`
- staged local CRUD/session management through the evidence CLI

This document explains both the current milestone and the larger future pipeline it supports.

## Current Repo Context

- The public API includes skill selection through `SkillSelectRequest`/`SkillSelectResponse` in `app/skill_selection/models.py`.
- Implemented methods today are `baseline`, `embeddings`, and `llm`.
- `baseline_filter` can pre-handle deterministic matches before model-backed second-pass scoring.
- Baseline remains the required fallback and deterministic safety path.
- The project-selection subsystem is exposed through `POST /select-projects` for explicit project candidates.
- The repo now also ships `resume_evidence`, which validates and loads `user/resume_evidence/projects.yaml` and `user/resume_evidence/skills.yaml`.
- The repo reserves `resume_generation/` for future orchestration that loads evidence, calls selection services, and prepares structured fill data.
- Evaluation assets already exist in `data/eval_cases/` and `scripts/eval.py`.

## Shared Contract

- Canonical skill categories remain exactly: `technology`, `programming`, `concepts`.
- Skill-selection outputs must always be a strict subset of the user-provided skills for the same category.
- Baseline must keep working if embeddings or LLM-based methods fail.
- All public JSON examples use snake_case and match the existing `/select-skills` shape unless a doc explicitly introduces a future schema.
- Model-backed branches route outbound calls through service/client layers, not scattered direct calls.
- Grounded resume work must keep user evidence inspectable and avoid unsupported claim generation.

## Implemented Branch 03 Milestone

### Canonical evidence root

User-authored resume evidence now lives under:

- `user/resume_evidence/`

The implemented schemas in that root today are:

- `user/resume_evidence/projects.yaml`
- `user/resume_evidence/skills.yaml`

### Implemented `projects.yaml` schema

The implemented root shape is:

```yaml
schema_version: 1
projects:
  - id: project-id
    name: Project Name
    summary: Grounded summary
    highlights:
      - Evidence-backed highlight
    active: true
    skills:
      technology: []
      programming: []
      concepts: []
    links: []
```

Required fields:

- `id`
- `name`
- `summary`
- `highlights`
- `active`
- `skills`

Optional field:

- `links`

Validation rules currently implemented:

- extra fields are forbidden
- duplicate project IDs are rejected
- `schema_version` is locked to `1`
- `highlights` must be non-empty
- skill buckets must match the shared three-category taxonomy

### Implemented `skills.yaml` schema

The implemented root shape is:

```yaml
schema_version: 1
skills:
  technology: []
  programming: []
  concepts: []
```

Validation rules currently implemented:

- extra fields are forbidden
- `schema_version` is locked to `1`
- skill buckets must match the shared three-category taxonomy

### Runtime integration

The implemented runtime flow is:

```text
user/resume_evidence/*.yaml
  -> load_registered_evidence()
  -> typed evidence validation
  -> app.state.resume_evidence
```

This is the first concrete runtime evidence hook for the future resume engine.

### Local evidence management

The CLI entrypoint is:

```bash
python -m resume_evidence.cli
```

The module layout now keeps CLI components under `resume_evidence/cli/`:

- `__init__.py` parses arguments and dispatches by schema
- `projects.py`, `skills.py`, `education.py`, `experience.py`, and `user.py` contain schema-specific commands
- `base.py` and `selection_ui.py` contain shared interactive helpers

Supported workflow today:

- list current staged projects
- inspect a project with `show`
- create a project with auto-generated hidden IDs
- edit or delete projects in staged state
- switch to `--schema skills`, `education`, `experience`, or `user` for the other registered evidence schemas
- confirm `apply` before writing to disk
- discard staged changes with `reload` or `quit`

## Current Use Cases

### Use case: skill-section targeting

Use `/select-skills` when you already have user-provided skills and want deterministic or model-assisted prioritization for a target role.

Examples:

- choose the most relevant skills for a backend resume
- run deterministic baseline selection only
- use `baseline_filter` so obvious matches stay deterministic while ambiguous skills go through embeddings or LLM scoring
- benchmark skill-selection quality with `scripts/eval.py`

### Use case: grounded project evidence management

Use `projects.yaml` and the CLI when you want a local, inspectable source of truth for project claims before higher-level resume generation exists.

Examples:

- keep project summaries and highlights in validated YAML
- manage staged edits without hand-editing the file directly
- preserve categorized project skills that align with the existing skill-selection taxonomy
- prepare evidence records that future synthesis can reuse

### Use case: grounded skills evidence management

Use `skills.yaml` and `python -m resume_evidence.cli --schema skills` when you want the canonical resume skill inventory stored as validated categorized lists.

Examples:

- keep resume skills grounded in user-authored YAML
- edit category buckets without hand-editing the file directly
- preserve the shared `technology` / `programming` / `concepts` taxonomy for later synthesis

### Use case: job-targeted project ranking

Use `/select-projects` when you have explicit project candidates and want to rank them for a target job without generating new claims.

Examples:

- rank project IDs for a backend job using deterministic baseline scoring
- use LLM scoring with local validation and baseline fallback
- keep project summaries and highlights out of the selection response while preserving traceability through IDs

## Future Pipeline

The broader Branch 03 target remains:

```text
user/resume_evidence/*.yaml
  -> deterministic load/validate/index
  -> resume_generation orchestration and synthesis/extraction
  -> structured fill data with provenance
  -> deterministic assembly
  -> generated resume artifact
```

Planned next layers:

- additional evidence files
  - `user/resume_evidence/profile.yaml`
  - `user/resume_evidence/experience.yaml`
- broader runtime evidence index across multiple files
- synthesis/extraction under `resume_generation/` that uses job target, evidence, and selected skills/projects
- resume format definitions owned by the generation layer
- deterministic assembly of full resume output

## Grounding Rules

- generated claims must be supported by user evidence
- job descriptions may guide prioritization, but they are not evidence of user experience
- unsupported claims must be omitted, not guessed
- generated artifacts must not silently mutate source evidence files
- skill selection is one prioritization signal, not the full source of truth for resume generation

## Agent Guidance

- Treat this document as both milestone status and future design guidance.
- `projects.yaml` and `skills.yaml` are implemented; do not describe them as merely hypothetical.
- `profile.yaml`, `experience.yaml`, synthesis, and assembly remain future work unless explicitly implemented.
- Keep new resume-generation work grounded, testable, and inspectable before adding prose-heavy or model-dependent layers.
