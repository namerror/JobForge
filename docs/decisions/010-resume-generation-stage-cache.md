# 010. Resume Generation Stage Cache

Date: 2026-06-20

## Status

Accepted

## Context

The resume-generation pipeline calls several HTTP stages that can spend LLM tokens:
skill selection, project selection, link scanning, and project bullet generation. If one
later stage fails, rerunning the whole pipeline repeats already-completed work and spends
tokens again.

The cache needs to support local development and single-user generation runs without adding
database dependencies or changing the service API contracts.

## Decision

Add an opt-in stage-output cache for `resume_generation/` orchestration.

- Cache entries are JSON files under `user/resume_generation/cache/` by default.
- Cache keys are SHA-256 hashes of the stage name plus the normalized outgoing request
  payload.
- Selection stages cache one entry per endpoint request.
- Link scanning and bullet-point generation cache one entry per project request.
- Writes use a temporary file and `os.replace` for atomic replacement.
- `cache.force_refresh` bypasses cache reads and rewrites entries.
- The cache is single-process only and does not use file locking.
- Deterministic local assembly remains uncached.

## Consequences

### Positive

- Failed runs can resume from the last completed expensive stage.
- Exact payload hashing naturally invalidates cache entries when evidence, job target, or
  generation settings change.
- JSON files stay inspectable and require no new dependency.

### Negative

- Cache storage can grow without an eviction policy.
- Concurrent writers are not protected.
- A malformed cache entry is treated as a miss, so the pipeline may repeat work in that case.

### Neutral

- The pipeline public entrypoint keeps returning `None` while final artifact output remains
  unfinished.
- Cache behavior is controlled through `user/resume_generation/config.yaml`.

## Alternatives Considered

- Whole-pipeline cache: rejected because it does not recover from mid-run failures.
- Manual run-id resume only: rejected because exact input hashing is safer and easier to use
  during iterative job-target edits.
- SQLite cache: deferred because the current workload does not need transactional queries or
  multi-process writes.
