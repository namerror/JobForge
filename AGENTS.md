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

### Add tests
1. Add test cases in `tests/test_role_profiles.py` for new profiles or edge cases
2. Test function logic directly with controlled inputs to ensure deterministic outputs

## Don'ts
- Don't add new features without tests.
- Don't modify existing role profiles without a clear reason and corresponding test updates.
- Don't introduce non-determinism in the baseline method.
- Don't make changes without logging them in `docs/dev-log.md` unless trivial (typo fixes, formatting).

## Development Logging (required)

After completing any non-trivial task or making architectural decisions, you MUST document your work in the appropriate log file.

### Session Log (`docs/dev-log.md`)
After completing tasks, append an entry with:
- **Date & Summary**: ISO date + brief task description (1 line)
- **Changes**: Files modified/created with line references where relevant
- **Rationale**: Why you made certain decisions or chose this approach
- **Tests**: What tests were added/modified and what they validate
- **Impact**: What this enables, fixes, or unlocks for future work

**Format:**
```markdown
### YYYY-MM-DD - [Brief Summary]

**Changes:**
- `path/to/file.py:10-25` - Description of change
- `tests/test_file.py` - Added tests for X

**Rationale:**
Explain why these changes were made and key decisions...

**Tests:**
- test_name: what it validates
- test_edge_case: what scenario it covers

**Impact:**
What this enables or fixes...
```

### Changelog (`docs/CHANGELOG.md`)
For user-facing changes, update using [Keep a Changelog](https://keepachangelog.com/) format:
- **Added**: new features
- **Changed**: changes to existing functionality
- **Fixed**: bug fixes
- **Removed**: removed features

Keep entries in the `[Unreleased]` section until a version is tagged.

### Decision Records (`docs/decisions/`)
For significant architectural choices, create numbered ADRs (Architectural Decision Records):
- Format: `NNN-short-title.md` (e.g., `001-baseline-scoring.md`)
- Include: Context, Decision, Consequences, Alternatives Considered
- These are permanent records - don't modify old ADRs, create new ones instead

### When NOT to log
- Trivial changes (typo fixes, minor formatting)
- Exploratory work that gets reverted
- Changes explicitly marked as temporary experiments
