# JobForge Resume Engine

JobForge is in a transition from a resume-generation prototype into a FastAPI-backed resume service. The current repo can already run grounded resume generation locally, and the recommended service direction is to keep the FastAPI backend as the integration point for product-facing APIs.

Today the repo ships three capability tracks:

- a FastAPI backend in `app/` with reusable data-processing and generation capabilities
- a grounded evidence engine in `resume_evidence/` for strict schemas, deterministic loading, and local CRUD workflows
- a resume orchestration pipeline in `resume_generation/` that reads `user/resume_generation/` and `user/resume_evidence/`, calls the FastAPI backend, and assembles resume artifacts

The current `user/` tree is local development data and runtime output. It is useful for prototyping and file-backed operation, but it should be treated as a storage adapter target rather than the final production persistence model.

## Vision

The long-term goal is a resume service that assembles targeted (job-specific) resumes from user-authored evidence without inventing claims. The intended pipeline is:

```text
user-authored evidence files
  -> deterministic load/validate/index
  -> grounded synthesis/extraction
  -> deterministic assembly
  -> generated resume artifact
```

Job descriptions can influence prioritization, but they are not evidence. Supported claims must trace back to user-authored source files.

## Implemented Today

### Skill selection API

The current public API is a FastAPI service for ranking user-provided skills by category for a target role.

- `POST /select-skills`
  - deterministic `baseline` method
  - `embeddings` method with cached OpenAI embeddings
  - `llm` method with local validation and deterministic ranking
  - optional `baseline_filter` that lets deterministic matches bypass model-backed scoring
  - required fallback to baseline behavior when model-backed methods fail
- `GET /health`
  - reports service liveness and effective config
- `GET /metrics-lite`
  - reports request totals, error totals, average latency, total model tokens, and effective method usage

Skill selection remains constrained by the repo invariants:

- outputs must stay within the user-provided skill set
- category boundaries remain `technology`, `programming`, and `concepts`
- deterministic ordering is required
- baseline must remain functional even if embeddings or LLM methods fail

### Grounded resume evidence foundation

The first implemented milestone is the `resume_evidence` package.

- `resume_evidence/models.py`
  - strict Pydantic models for all registered evidence YAML schemas
- `resume_evidence/loader.py`
  - schema registry and deterministic YAML loading
- `resume_evidence/session.py`
  - staged in-memory CRUD with validation-before-mutation and atomic apply-to-disk writes
- `resume_evidence/cli/`
  - CLI entrypoint and schema dispatcher
- `resume_evidence/cli/base.py`
  - shared interactive CLI base helpers
- `resume_evidence/cli/{projects,skills,education,experience,user}.py`
  - schema-specific command implementations
- `resume_generation/`
  - evidence-to-selection orchestration, bullet-point generation, intermediate result assembly, and LaTeX artifact rendering
- `app/main.py`
  - loads registered evidence on startup into `app.state.resume_evidence`

The currently implemented evidence schemas are:

- `user/resume_evidence/projects.yaml`
  - `schema_version: 1`
  - strict project records with `id`, `name`, `summary`, `highlights`, `active`, `skills`, and optional `links`
- `user/resume_evidence/skills.yaml`
  - `schema_version: 1`
  - strict categorized skill lists under `technology`, `programming`, and `concepts`
- `user/resume_evidence/education.yaml`
  - `schema_version: 1`
  - strict education records with `name`, `degree`, `grade`, `start`, optional `end`, `location`, and `relevant_coursework`
- `user/resume_evidence/experience.yaml`
  - `schema_version: 1`
  - strict experience records with `id`, `name`, `role`, `summary`, `highlights`, `active`, `skills`, `location`, `start`, optional `end`, and optional `links`
- `user/resume_evidence/user.yaml`
  - `schema_version: 1`
  - strict basic contact info with required `name`, `email`, and `phone`, plus optional `linkedin`, `github`, and `website`

Resume evidence should be managed by users via the CLI or by other tools that write to the `user/resume_evidence/` directory.

### Project selection API

The project-selection subsystem ranks explicit project candidates for a job target without generating resume prose.

- `POST /select-projects`
  - accepts `context` with job title/description and explicit project `candidates`
  - supports deterministic `baseline` and model-backed `llm` methods
  - validates LLM project-id scores locally and falls back to baseline when needed
  - returns project IDs and scores, not project summaries, highlights, links, or generated claims

### Evidence CLI workflow

Use the CLI to manage staged edits to evidence YAML without hand-editing:

```bash
PYTHONPATH=. python -m resume_evidence.cli
```

Default `projects` commands:

- `list`
- `show <index>`
- `create`
- `edit <index>`
- `delete <index>`
- `apply`
- `reload`
- `quit`

The default schema is `projects`. Use `--schema` to manage any registered evidence file:

```bash
PYTHONPATH=. python -m resume_evidence.cli --schema skills
PYTHONPATH=. python -m resume_evidence.cli --schema education
PYTHONPATH=. python -m resume_evidence.cli --schema experience
PYTHONPATH=. python -m resume_evidence.cli --schema user
```

Projects, education, and experience support list/show/create/edit/delete/apply/reload/quit workflows. Skills and user info support list/show-style inspection, edit, apply, reload, and quit.

The CLI keeps edits staged in memory until `apply` is confirmed, preserves stable hidden IDs for projects and experience entries, and writes atomically to disk.

### Evaluation and support scripts

The repo also includes utilities for skill-selection evaluation and data preparation:

- `scripts/build_skill_pools.py`
  - builds normalized skill pools
- `scripts/eval_cases_generator.py`
  - generates evaluation datasets
- `scripts/eval.py`
  - runs skill-selection evaluation against case files

See [scripts/README.md](/home/leon/Documents/proj/JobForge/scripts/README.md) for command details.

## How The Pieces Fit Together

JobForge now has a broader resume-engine shape:

- the FastAPI `app/` layer provides reusable backend capabilities for selection, focus derivation, bullet generation, enrichment, metrics, and health checks
- the skills API helps prioritize and rank skills for the Skills section
- the project-selection API helps prioritize grounded projects for a target job
- the top-level resume-evidence package establishes grounded source-of-truth data under `user/resume_evidence/`
- the `resume_generation/` layer combines target job context, evidence, and selected service outputs into an intermediate resume result
- deterministic assembly and LaTeX rendering turn that structured result into resume artifacts without inventing claims

Skill selection is no longer the whole project. It is one subsystem inside the larger grounded resume pipeline.

## Recommended Service Architecture

The recommended next phase is to integrate the evidence and generation layers into the FastAPI backend through a product-facing facade while keeping the existing stage endpoints as internal backend capabilities.

### Product-facing facade

Future product clients should call higher-level resume service APIs, not orchestrate every generation stage themselves. The facade should own:

- evidence CRUD over the schemas currently implemented by `resume_evidence`
- generation-run creation with a job target and selected evidence scope
- generation-run status and artifact retrieval
- structured resume result retrieval for web-app editing or rendering

The current stage APIs remain valuable, but they are better treated as internal capabilities that the facade calls.

### Internal capability APIs

The existing FastAPI routes are useful backend building blocks:

- `/select-skills`
- `/select-projects`
- `/derive-job-focus`
- `/generate-bulletpoints`
- `/scan-link` and `/enrich-link-evidence`

As the service boundary matures, these routes should either move behind an internal namespace or be documented separately from the product API. That keeps the future web app from depending on orchestration details such as cache keys, prompt-specific payloads, or per-stage retry behavior.

### Storage transition

Keep the current YAML-backed `user/resume_evidence/` and `user/resume_generation/` layout for local development and prototype runs. The next implementation step should introduce repository/adapter interfaces around evidence, generation runs, cache entries, and artifacts. The first adapter can continue to read and write files; a database-backed adapter can follow when service requirements are clearer.

This avoids an early database dependency while preventing file paths from leaking into the final API design.

### Generation run model

Full resume generation should be exposed as an async run:

```text
POST create generation run
  -> return run_id
GET run status
  -> queued | running | succeeded | failed
GET run result/artifacts
  -> structured result, manifest, rendered output
```

The current local CLI-style pipeline can remain synchronous internally, but the product API should not require a web client to hold a request open across multiple LLM-backed stages.

## Resume Generation Usage

Resume generation runs from `resume_generation/main.py`. It reads generation settings, the target job, and all registered evidence files, then calls the running FastAPI app over HTTP for selection, job focus derivation, and bullet generation. Link scanning is exposed as a standalone evidence-enrichment capability rather than part of the normal generation pipeline.

Start the app first:

```bash
uvicorn app.main:app --reload
```

Then run the generation pipeline from the repo root:

```bash
PYTHONPATH=. python -m resume_generation.main
```

The direct module entrypoint writes:

- `user/resume_generation/resume_result.json` - intermediate structured resume data
- `user/resume_generation/resume.tex` - LaTeX resume output, unless `resume_output.path` overrides it
- `user/resume_generation/resume.pdf` - optional rendered PDF when `resume_output.render_pdf: true`

To render an existing `.tex` file without rerunning the full pipeline:

```bash
PYTHONPATH=. python -m resume_generation.pdf
```

The PDF renderer uses local `latexmk`, so the runtime environment needs TeX Live plus `latexmk` installed when `resume_output.render_pdf: true`.

`user/resume_generation/config.yaml` controls the local orchestration:

- `app` - FastAPI base URL and request timeout used by the pipeline
- `skill_selection` - method, `top_n`, baseline-filter toggle, debug mode, and LLM overrides sent to `/select-skills`
- `project_selection` - method, `top_n`, debug mode, and LLM overrides sent to `/select-projects`; `top_n: null` omits the request override and lets the app's `PROJ_TOP_N` default decide the limit
- `job_focus_generation` - LLM overrides for one job-focus derivation per target role
- `link_scanning` - standalone enrichment settings used by the link enrichment runner
- `project_bullet_point_generation` - bullet count range, debug mode, and LLM overrides for selected projects
- `experience_bullet_point_generation` - bullet count range, debug mode, and LLM overrides for active experience records
- `cache` - stage cache toggle, path override, and force-refresh behavior
- `resume_output` - optional `.tex` output path plus opt-in PDF rendering settings

`user/resume_generation/job_target.yaml` supplies the target role:

- `schema_version: 1`
- `title` - required job title
- `description` - optional job description text used for selection and bullet generation context

The pipeline loads every registered resume-evidence schema from `user/resume_evidence/`:

- `user.yaml` - contact/header data for the resume top section
- `education.yaml` - education entries and relevant coursework
- `experience.yaml` - active work experience entries and evidence for experience bullets
- `projects.yaml` - active project candidates, highlights, skills, and optional links
- `skills.yaml` - categorized skills available for the Skills section

Only `active: true` projects are sent to project selection, and only selected projects are sent to project bullet generation. Only `active: true` experience entries are assembled into the final experience section.

## API

### Health

`GET /health`

Example response:

```json
{
  "status": "ok",
  "version": "0.2.0",
  "service": "jobforge-resume-engine",
  "dev_mode": true,
  "skill_selection": {
    "method": "baseline",
    "top_n": 10,
    "baseline_filter": false,
    "llm_model": "gpt-5-mini",
    "llm_max_output_tokens": 1200
  },
  "project_selection": {
    "method": "llm",
    "top_n": null,
    "llm_model": "gpt-5-mini",
    "llm_max_output_tokens": 1200
  },
  "link_scanning": {
    "enabled": false,
    "llm_model": "gpt-5-mini",
    "llm_max_output_tokens": 1200
  }
}
```

### Select Skills

`POST /select-skills`

Example request:

```json
{
  "job_role": "AI/ML Engineer",
  "job_text": "Optional job description text",
  "technology": ["Docker", "Kubernetes", "AWS", "PostgreSQL", "TensorFlow"],
  "programming": ["Python", "TypeScript", "SQL"],
  "concepts": ["Machine Learning", "CI/CD", "Distributed Systems"],
  "top_n": 5,
  "method": "embeddings",
  "baseline_filter": true,
  "dev_mode": true
}
```

Example response:

```json
{
  "technology": ["TensorFlow", "AWS", "Docker"],
  "programming": ["Python"],
  "concepts": ["Machine Learning", "Distributed Systems"],
  "details": {}
}
```

### Select Projects

`POST /select-projects`

Example request:

```json
{
  "context": {
    "title": "Backend Engineer",
    "description": "Build Python APIs with Django and PostgreSQL."
  },
  "candidates": [
    {
      "id": "jobforge",
      "name": "JobForge",
      "summary": "Resume engine with deterministic selection and grounded evidence.",
      "skills": {
        "technology": ["Django", "PostgreSQL"],
        "programming": ["Python"],
        "concepts": ["API"]
      }
    }
  ],
  "method": "baseline",
  "top_n": 1,
  "dev_mode": true
}
```

Example response:

```json
{
  "selected_project_ids": ["jobforge"],
  "ranked_projects": [
    {
      "project_id": "jobforge",
      "score": 0.75,
      "method": "baseline"
    }
  ],
  "details": {}
}
```

### Metrics

`GET /metrics-lite`

Example response:

```json
{
  "requests_total": 42,
  "errors_total": 1,
  "total_tokens": 12000,
  "avg_latency_ms": 25.3,
  "method_usage": {
    "baseline": 30,
    "embeddings": 8,
    "llm": 4
  },
  "subsystems": {
    "skill_selection": {
      "requests_total": 38,
      "errors_total": 1,
      "total_tokens": 9000,
      "avg_latency_ms": 22.1,
      "method_usage": {
        "baseline": 30,
        "embeddings": 8
      }
    },
    "project_selection": {
      "requests_total": 4,
      "errors_total": 0,
      "total_tokens": 3000,
      "avg_latency_ms": 55.7,
      "method_usage": {
        "llm": 4
      }
    }
  }
}
```

`method_usage` reflects the method that actually produced the response. If a model-backed method falls back to baseline, the request is counted under `baseline`. The top-level metrics remain aggregate; `subsystems` breaks out skill selection and project selection.

## Configuration

JobForge reads settings from environment variables via `app/config.py`.

```bash
SKILL_METHOD=baseline # available options: baseline, embeddings, llm
SKILL_TOP_N=10 # how many top-ranked skills to return per category
SKILL_BASELINE_FILTER=false # if true, deterministic skill matches bypass model-backed scoring

PROJ_METHOD=llm # available options: baseline, llm
# PROJ_TOP_N=2 # optional; omit to return all ranked projects unless the request overrides it

DEV_MODE=true # return debugging info
LOG_LEVEL=INFO

OPENAI_API_KEY=your_key_here

EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_BATCH_SIZE=100

SKILL_LLM_MODEL=gpt-5-mini
SKILL_LLM_MAX_OUTPUT_TOKENS=1200
PROJ_LLM_MODEL=gpt-5-mini
PROJ_LLM_MAX_OUTPUT_TOKENS=1200
LINK_SCANNING_ENABLED=false
LINK_SCANNING_LLM_MODEL=gpt-5-mini
LINK_SCANNING_LLM_MAX_OUTPUT_TOKENS=1200
```

`OPENAI_API_KEY` is only required for skill-selection `embeddings`, skill-selection `llm`, project-selection `llm`, bullet-point generation, and enabled link-scanning requests.
Link scanning treats normal URLs as single-page sources; `github.com/{owner}/{repo}` links allow repository-scoped exploration for technical project evidence.
Legacy generic selection variables such as `METHOD`, `TOP_N`, `BASELINE_FILTER`, `LLM_MODEL`, and `LLM_MAX_OUTPUT_TOKENS` are no longer read.
Baseline filtering is skill-selection-only; project selection does not define a baseline pre-filter pass yet.

## Running Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI app:

```bash
uvicorn app.main:app --reload
```

Run the evidence CLI:

```bash
PYTHONPATH=. python -m resume_evidence.cli
```

Run a specific evidence schema CLI:

```bash
PYTHONPATH=. python -m resume_evidence.cli --schema skills
PYTHONPATH=. python -m resume_evidence.cli --schema education
PYTHONPATH=. python -m resume_evidence.cli --schema experience
PYTHONPATH=. python -m resume_evidence.cli --schema user
```

Run resume generation after the app is running:

```bash
PYTHONPATH=. python -m resume_generation.main
```

## Tests

Tests assume the repo root is on `PYTHONPATH`:

```bash
export PYTHONPATH=.
pytest
```

Useful targeted runs:

```bash
PYTHONPATH=. pytest tests/test_resume_evidence.py
PYTHONPATH=. pytest tests/test_resume_evidence_cli.py
PYTHONPATH=. pytest tests/test_integration.py
```

## Planned Next

The next backend transition should focus on service integration rather than adding unrelated generation features:

- add repository/adapter boundaries around evidence files, generation runs, cache entries, and artifacts
- add a product-facing FastAPI facade for evidence CRUD and async resume-generation runs
- keep the current stage endpoints available as internal capabilities for the facade and tests
- defer database persistence until the adapter contract and product API shape are stable
- expand output formats only after the structured result and run lifecycle are service-ready

See:

- [docs/architecture-overview.md](/home/leon/Documents/proj/JobForge/docs/architecture-overview.md)
- [docs/decisions/003-grounded-resume-evidence-pipeline.md](/home/leon/Documents/proj/JobForge/docs/decisions/003-grounded-resume-evidence-pipeline.md)
- [docs/decisions/004-user-resume-evidence-root-and-projects-milestone.md](/home/leon/Documents/proj/JobForge/docs/decisions/004-user-resume-evidence-root-and-projects-milestone.md)
- [docs/decisions/005-subsystem-package-organization.md](/home/leon/Documents/proj/JobForge/docs/decisions/005-subsystem-package-organization.md)
- [docs/decisions/008-standalone-resume-evidence-and-generation-layers.md](/home/leon/Documents/proj/JobForge/docs/decisions/008-standalone-resume-evidence-and-generation-layers.md)
- [docs/decisions/012-fastapi-resume-service-transition.md](/home/leon/Documents/proj/JobForge/docs/decisions/012-fastapi-resume-service-transition.md)

## Current Limitations

- JobForge does not yet ship a public full-resume generation API.
- Resume generation currently runs as a local orchestration module, not as a public HTTP endpoint.
- The current output path is structured JSON plus LaTeX; additional export formats are still future work.
