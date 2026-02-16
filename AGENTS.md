# AGENTS.md — Agent Playbook

This repo is designed to be edited by coding agents (Claude Code, Codex, etc.) safely.

## Organization
- Tests in `tests/`
- Scoring logic in `app/scoring/`

## Repository invariants
- Never add skills that weren't provided in the request.
- Category boundaries are respected: Technology / Programming / Concepts.
- Stable deterministic ordering is required.
- Baseline method must remain functional even if embeddings/hybrid fails.

## How agents should work in this repo
### Make small, runnable changes
- Prefer small PR-style diffs.
- Each change includes tests.
- Update `docs/decisions.md` when making architectural choices.

### Avoid accidental scope creep
- This service does not generate resumes, bullet points, or job analysis.
- Do not add database dependencies early.
- Do not add LLM dependencies without:
  1) baseline success
  2) evaluation harness dataset
  3) measured improvement

## Common tasks
### Add a new role profile
1. Create a new profile in `app/scoring/role_profiles.py` with relevant keywords
2. Ensure baseline scorer uses profile data deterministically

### Add unit tests
1. Add test cases in `tests/test_role_profiles.py` for new profiles or edge cases
2. Test function logic directly with controlled inputs to ensure deterministic outputs

## Don'ts
- Don't add new features without tests.
- Don't modify existing role profiles without a clear reason and corresponding test updates.
- Don't introduce non-determinism in the baseline method.
