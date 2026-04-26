# Agent Context Index

Use this file as the primary navigation index for coding agents.

## Canonical Instruction Files

1. `AGENTS.md`
   - repository invariants, scope guardrails, and logging requirements
2. `CLAUDE.md`
   - repo-specific workflow and quality constraints

## Core Project Context

1. `README.md`
   - current product framing, implemented capabilities, and project vision
2. `docs/architecture-overview.md`
   - module relationships, startup flow, skill-selection runtime flow, and the implemented evidence layer
3. `docs/branch-03-grounded-resume-generation.md`
   - current Branch 03 milestone plus future grounded resume pipeline direction
4. `docs/branch-03-project-selection-plan.md`
   - internal project ranking milestone for job-targeted grounded resume evidence
5. `docs/decisions/003-grounded-resume-evidence-pipeline.md`
   - original architecture decision for the grounded evidence pipeline
6. `docs/decisions/004-user-resume-evidence-root-and-projects-milestone.md`
   - superseding decision for the `user/resume_evidence/` root and the implemented projects-evidence milestone

## Recommended Read Order

1. `AGENTS.md`
2. `CLAUDE.md`
3. `README.md`
4. `docs/architecture-overview.md`
5. `app/main.py`
6. `app/services/skill_selector.py`
7. `app/scoring/baseline.py`
8. `app/scoring/role_profiles.py`
9. `app/resume_evidence/loader.py`
10. `app/resume_evidence/session.py`
11. `app/project_selection/selector.py`
12. `docs/branch-03-grounded-resume-generation.md`
13. `docs/project-selection-plan.md`
14. `docs/decisions/003-grounded-resume-evidence-pipeline.md`
15. `docs/decisions/004-user-resume-evidence-root-and-projects-milestone.md`

## Resume Evidence Entry Points

- `app/resume_evidence/models.py`
  - strict runtime models for `projects.yaml`
- `app/resume_evidence/loader.py`
  - evidence registry and startup loading
- `app/resume_evidence/session.py`
  - staged CRUD/session logic
- `app/resume_evidence/cli.py`
  - interactive evidence-management CLI
- `user/resume_evidence/projects.yaml`
  - currently implemented source-of-truth evidence file

## Project Selection Entry Points

- `app/project_selection/selector.py`
  - internal `select_projects(...)` entrypoint for ranking explicit project candidates
- `app/project_selection/baseline.py`
  - deterministic project scoring from baseline skill matches and text overlap
- `app/project_selection/llm.py`
  - LLM-backed project scoring with local validation and baseline fallback
- `app/services/project_llm_client.py`
  - OpenAI Responses API wrapper for project relevance scoring
