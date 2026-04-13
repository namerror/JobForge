# Development Log

This folder contains per-session development logs documenting all non-trivial agent work.

---

## Naming Convention

Files must follow the pattern: **`MM-DD-YYYY-AgentName-short-description.md`**

- `MM-DD-YYYY` — date the session was completed
- `AgentName` — the agent or tool that performed the work (e.g., `Claude`, `Copilot`, `Codex`, `GPT4o`)
- `short-description` — a few hyphenated words summarizing what was done

**Examples:**
- `03-07-2026-Copilot-optimize-logging-instructions.md`
- `03-08-2026-Claude-add-role-profile-tests.md`
- `02-16-2026-Codex-baseline-scoring-test-suite.md`

## Required Content

Each session file must include:

- **Agent & Model** — agent name and specific model version (e.g., Claude Sonnet 4.5, GPT-4o)
- **Date & Summary** — ISO date + one-line task description
- **Changes** — files modified/created with line references where relevant
- **Rationale** — why these decisions were made
- **Tests** — tests added/modified and what they validate
- **Impact** — what this enables, fixes, or unlocks

## What Belongs Here vs. CHANGELOG

| Type of change | Goes in… |
|---|---|
| New user-facing feature | `docs/CHANGELOG.md` AND a session file here |
| Bug fix | Session file here only |
| Adding/updating tests | Session file here only |
| Internal refactor / implementation tweak | Session file here only |
| Documentation update | Session file here only |
| Trivial (typo fix, minor formatting) | Neither — no log needed |

---

## Session Index

- `2026-04-13-Codex-baseline-filtered-skill-selection.md` - Implement baseline-filtered skill selection
- `04-13-2026-Codex-revise-baseline-filter-plan.md` - 2026-04-13 - Revise Branch 01 baseline filter plan
- `04-11-2026-Codex-metrics-effective-method-and-tokens.md` - 2026-04-11 - Track total tokens and fallback method usage
- `04-11-2026-Codex-llm-model-parameter-compatibility.md` - 2026-04-11 - Fix LLM model parameter compatibility
- `04-10-2026-Codex-llm-skill-selection.md` - 2026-04-10 - Implement LLM skill selection
- `04-08-2026-Codex-add-parallel-branch-plans.md` - 2026-04-08 - Add parallel branch planning docs for hybrid, LLM, and grounded resume work
- `03-07-2026-Copilot-optimize-logging-instructions.md` - 2026-03-07 - Optimize agent logging instructions
- `2026-03-06-embeddings-caching-bug-fix-and-tests.md` - 2026-03-06 - Fix embeddings stale kwarg bug and add unit tests
- `2026-03-04-embeddings-scorer.md` - 2026-03-04 - Implement embeddings scorer
- `2026-03-04-2026-03-04-fix-embedding-client-validation-and-logging.md` - 2026-03-04 - Fix embedding client validation and logging
- `2026-03-04-review-embedding-scoring-and-rate-limit.md` - 2026-03-04 - Review embedding scoring and rate limit
- `2026-02-25-split-dev-log-into-sessions.md` - 2026-02-25 - Split dev log into session files
- `2026-02-25-2026-02-25-add-agent-architecture-overview-and-instruction-index.md` - 2026-02-25 - Add agent architecture overview and instruction index
- `2026-02-24-2026-02-24-migrate-role-profiles-from-python-dict-to-yaml-files.md` - 2026-02-24 - Migrate role profiles from Python dict to YAML files
- `2026-02-17-2026-02-17-implement-eval-case-scoring-function.md` - 2026-02-17 - Implement eval_case scoring function
- `2026-02-17-2026-02-17-expand-eval-cases-to-20-realistic-user-inputs.md` - 2026-02-17 - Expand eval cases to 20 realistic user inputs
- `2026-02-16-2026-02-16-add-comprehensive-tests-for-baseline-select-skills-function.md` - 2026-02-16 - Add comprehensive tests for baseline_select_skills() function
- `2026-02-16-2026-02-16-complete-test-suite-for-baseline-scoring.md` - 2026-02-16 - Complete test suite for baseline scoring
