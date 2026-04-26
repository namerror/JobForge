# Architectural Decision Records

This directory contains records of significant architectural and design decisions made during development.

## Format

Each ADR follows this structure:

```markdown
# [Number]. [Title]

Date: YYYY-MM-DD

## Status

[Proposed | Accepted | Deprecated | Superseded by ADR-XXX]

## Context

What is the issue we're trying to solve? What constraints exist?

## Decision

What did we decide to do and why?

## Consequences

### Positive
- What improves?
- What does this enable?

### Negative
- What trade-offs are we accepting?
- What complexity does this add?

### Neutral
- What are we committing to?

## Alternatives Considered

What other options were evaluated and why were they rejected?
```

## Naming Convention

Files are named: `NNN-short-kebab-case-title.md`

- `001-embedding-cache-persistence.md`
- `002-baseline-filter-selection.md`
- `003-grounded-resume-evidence-pipeline.md`

## Current ADRs

- `001-embedding-cache-persistence.md`
- `002-baseline-filter-selection.md`
- `003-grounded-resume-evidence-pipeline.md`
- `004-user-resume-evidence-root-and-projects-milestone.md`
- `005-subsystem-package-organization.md`
