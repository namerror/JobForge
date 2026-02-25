# Agent Context Index

Use this file as the primary navigation index for coding agents.

## Canonical Instruction Files

1. `AGENTS.md`
   - Repository invariants, scope guardrails, and logging requirements.
2. `CLAUDE.md`
   - Service-specific implementation workflow and quality constraints.

## Architecture and Flow

1. `docs/architecture-overview.md`
   - Module dependency map for `app/`
   - End-to-end request flow
   - Baseline scoring logic flow and deterministic behavior notes

## Recommended Read Order for Understanding the Codebase

1. `AGENTS.md`
2. `CLAUDE.md`
3. `docs/architecture-overview.md`
4. `app/main.py`
5. `app/services/skill_selector.py`
6. `app/scoring/baseline.py`
7. `app/scoring/role_profiles.py`
