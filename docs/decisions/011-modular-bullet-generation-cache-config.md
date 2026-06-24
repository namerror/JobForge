# 011. Modular Bullet Generation Cache Config

Date: 2026-06-24

## Status

Accepted

## Context

The resume-generation stage cache keys entries by stage name plus the outgoing
request payload. Project bullet generation and experience bullet generation used
the same `bullet_point_generation` config section, so changing one bullet model
changed both outgoing payload families and invalidated both cache groups.

The pipeline needs modular caching: changes to experience bullet generation must
not force project bullet generation to repeat, and changes to project bullet
generation must not force experience bullet generation to repeat.

## Decision

Split the resume-generation bullet configuration into two explicit sections:

- `project_bullet_point_generation`
- `experience_bullet_point_generation`

Project and experience bullet orchestration must read only their corresponding
section when building `/generate-bulletpoints` payloads. The legacy shared
`bullet_point_generation` key is rejected at config load time so runs cannot
silently keep shared invalidation behavior.

Project bullet cache entries use the `project_bullet_points` stage name.
Experience bullet cache entries keep using the `experience_bullet_points` stage
name. Cache response logging reports whether each stage response came from cache
or HTTP.

## Consequences

### Positive

- Bullet generation cache invalidation now follows the actual section-specific
  request payload.
- Model or token-budget changes for one bullet section do not regenerate the
  other section.
- The config file makes project-vs-experience tuning explicit.

### Negative

- Existing local configs using `bullet_point_generation` must be updated.
- Existing project bullet cache files under the old `bullet_points` stage will
  not be reused.

### Neutral

- The `/generate-bulletpoints` HTTP API remains unchanged.
- Service-level LLM defaults still matter only when the orchestration payload
  omits explicit request overrides.

## Alternatives Considered

- Keep `bullet_point_generation` as a fallback default with optional overrides:
  rejected because it preserves shared invalidation when fallback values change.
- Nest project and experience config under `bullet_point_generation`: rejected
  because separate sibling sections are simpler to validate and read.
