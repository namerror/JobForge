# Agent Context Index

Use this file as the primary navigation index for coding agents.

## Canonical Instruction Files

1. `AGENTS.md`
   - repository invariants, scope guardrails, and logging requirements
2. `CLAUDE.md`
   - repo-specific workflow and quality constraints

## Core Project Context

1. `README.md`
   - current product framing, implemented capabilities, service-transition direction, and project vision
2. `docs/architecture-overview.md`
   - module relationships, startup flow, runtime flows, implemented evidence/generation layers, and planned service facade
3. `docs/decisions/003-grounded-resume-evidence-pipeline.md`
   - original architecture decision for the grounded evidence pipeline
4. `docs/decisions/004-user-resume-evidence-root-and-projects-milestone.md`
   - superseding decision for the `user/resume_evidence/` root and the implemented projects-evidence milestone
5. `docs/decisions/005-subsystem-package-organization.md`
   - current subsystem layout and legacy import compatibility policy
6. `docs/decisions/008-standalone-resume-evidence-and-generation-layers.md`
   - top-level evidence and generation package boundary
7. `docs/decisions/009-bullet-point-generation-api-boundary.md`
   - current grounded bullet-point generation API boundary
8. `docs/decisions/012-fastapi-resume-service-transition.md`
   - recommended FastAPI facade, file-adapter, and async-run transition path
9. `docs/archive/branch-03-grounded-resume-generation.md`
   - historical Branch 03 plan; use only as background, not current implementation truth
10. `docs/archive/project-selection-plan.md`
   - historical project-selection plan; use implemented code and current ADRs first

## Recommended Read Order

1. `AGENTS.md`
2. `CLAUDE.md`
3. `README.md`
4. `docs/architecture-overview.md`
5. `app/main.py`
6. `app/skill_selection/selector.py`
7. `app/skill_selection/scoring/baseline.py`
8. `app/skill_selection/scoring/role_profiles.py`
9. `app/project_selection/service.py`
10. `app/project_selection/selector.py`
11. `resume_evidence/loader.py`
12. `resume_evidence/session.py`
13. `resume_generation/main.py`
14. `resume_generation/selection.py`
15. `resume_generation/bullet_points.py`
16. `resume_generation/assembly.py`
17. `docs/decisions/012-fastapi-resume-service-transition.md`
18. `docs/archive/branch-03-grounded-resume-generation.md`

## Skill Selection Entry Points

- `app/skill_selection/models.py`
  - request/response models for `/select-skills`
- `app/skill_selection/selector.py`
  - service wrapper for method dispatch, metrics, logging, and response shaping
- `app/skill_selection/scoring/`
  - baseline, embeddings, LLM ranking, role profiles, and synonym normalization
- `app/skill_selection/data/`
  - skill-selection role profiles, synonym map, and embedding caches

## Resume Evidence Entry Points

- `resume_evidence/models.py`
  - strict runtime models for all registered evidence YAML schemas
- `resume_evidence/loader.py`
  - evidence registry and startup loading
- `resume_evidence/session.py`
  - staged CRUD/session logic for resume evidence schemas
- `resume_evidence/cli/`
  - CLI entrypoint and schema dispatcher
- `resume_evidence/cli/base.py`
  - shared interactive CLI prompt and command helpers
- `resume_evidence/cli/{projects,skills,education,experience,user}.py`
  - schema-specific command implementations
- `user/resume_evidence/projects.yaml`
  - implemented project source-of-truth evidence file
- `user/resume_evidence/skills.yaml`
  - implemented skills source-of-truth evidence file
- `user/resume_evidence/education.yaml`
  - implemented education source-of-truth evidence file
- `user/resume_evidence/experience.yaml`
  - implemented experience source-of-truth evidence file
- `user/resume_evidence/user.yaml`
  - implemented basic user contact source-of-truth evidence file

## Resume Generation Entry Points

- `resume_generation/`
  - implemented resume generation orchestration package
- `resume_generation/main.py`
  - pipeline owner for config, job target, evidence loading, selection, job focus, bullet generation, assembly, manifest, and artifacts
- `resume_generation/selection.py`
  - `generate_selection_context(...)` HTTP selection stage over `/select-skills` and `/select-projects`
- `resume_generation/job_focus.py`
  - cached HTTP job-focus stage over `/derive-job-focus`
- `resume_generation/bullet_points.py`
  - project and experience HTTP bullet generation stages over `/generate-bulletpoints`
- `resume_generation/assembly.py`
  - deterministic assembly into the intermediate resume result schema
- `resume_generation/latex.py`
  - LaTeX artifact rendering from the intermediate resume result
- `resume_generation/config.py`
  - strict loading for `user/resume_generation/config.yaml` and `job_target.yaml`
- `user/resume_generation/config.yaml`
  - user-level HTTP and selection request options
- `user/resume_generation/job_target.yaml`
  - target job title and optional description for generation selection

## Project Selection Entry Points

- `app/project_selection/selector.py`
  - internal `select_projects(...)` entrypoint for ranking explicit project candidates
- `app/project_selection/service.py`
  - API-facing service wrapper with defaults, metrics, logging, and fallback tracking
- `app/project_selection/baseline.py`
  - deterministic project scoring from baseline skill matches and text overlap
- `app/project_selection/llm.py`
  - LLM-backed project scoring with local validation and baseline fallback
- `app/project_selection/llm_client.py`
  - OpenAI Responses API wrapper for project relevance scoring
