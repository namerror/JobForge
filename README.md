# Resume Engine

This project is evolving from a skill-selection microservice into a grounded resume-generation service. Today the repo ships three capability tracks:

- a production FastAPI API for skill selection with deterministic baseline, embeddings, and LLM methods
- a public project-selection API for ranking explicit user project candidates for a target job
- an implemented first milestone of the evidence-based resume pipeline centered on `user/resume_evidence/projects.yaml`

Selection services live under the FastAPI `app/` package, while evidence management now lives in top-level `resume_evidence/`. The top-level `resume_generation/` package is reserved for the future orchestration layer that will load evidence, call the selection services, and prepare structured resume fill data.

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
  - strict Pydantic models for `projects.yaml` and `skills.yaml`
- `resume_evidence/loader.py`
  - schema registry and deterministic YAML loading
- `resume_evidence/session.py`
  - staged in-memory CRUD with validation-before-mutation and atomic apply-to-disk writes
- `resume_evidence/cli.py`
  - CLI entrypoint and schema dispatcher
- `resume_evidence/base_cli.py`
  - shared interactive CLI base helpers
- `resume_evidence/projects_cli.py`
  - project-evidence command implementation
- `resume_evidence/skills_cli.py`
  - skills-evidence command implementation
- `resume_generation/`
  - reserved boundary for future evidence-to-selection orchestration and structured fill-data preparation
- `app/main.py`
  - loads registered evidence on startup into `app.state.resume_evidence`

The currently implemented evidence schemas are:

- `user/resume_evidence/projects.yaml`
  - `schema_version: 1`
  - strict project records with `id`, `name`, `summary`, `highlights`, `active`, `skills`, and optional `links`
- `user/resume_evidence/skills.yaml`
  - `schema_version: 1`
  - strict categorized skill lists under `technology`, `programming`, and `concepts`

These schemas should be managed by users via the CLI or by other tools that write to the `user/resume_evidence/` directory. Hand-editing is possible but not recommended, as the CLI provides validation and preserves stable hidden IDs for projects.

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

The default schema is `projects`. For skills evidence, use:

```bash
PYTHONPATH=. python -m resume_evidence.cli --schema skills
```

The skills CLI supports `list`, `edit`, `apply`, `reload`, and `quit`.

The CLI keeps edits staged in memory until `apply` is confirmed, preserves stable hidden IDs for projects, and writes atomically to disk.

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

- the skills API helps prioritize and rank skills for the future Skills section
- the project-selection API helps prioritize grounded projects for a target job
- the top-level resume-evidence package establishes grounded source-of-truth data under `user/resume_evidence/`
- the future `resume_generation/` layer will combine target job context, evidence, and selected service outputs into structured fill data
- future deterministic assembly will turn that structured fill data into resume output without inventing claims

Skill selection is no longer the whole project. It is one subsystem inside the larger grounded resume pipeline.

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

Run the skills evidence CLI:

```bash
PYTHONPATH=. python -m resume_evidence.cli --schema skills
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

The resume-generation pipeline is implemented from `resume_generation/main.py`: it loads evidence, reads `user/resume_generation/config.yaml` plus `job_target.yaml`, calls the running app's selection APIs over HTTP, and hands selected projects to bullet-point generation.

The following pieces are still planned for the broader public resume-generation flow:

- additional evidence files under `user/resume_evidence/`
  - `profile.yaml`
  - `experience.yaml`
- grounded synthesis/extraction under `resume_generation/` that returns structured resume fill data with provenance
- resume format definitions owned by the generation layer
- deterministic assembly that renders full resume artifacts from structured fill data

See:

- [docs/branch-03-grounded-resume-generation.md](/home/leon/Documents/proj/JobForge/docs/branch-03-grounded-resume-generation.md)
- [docs/architecture-overview.md](/home/leon/Documents/proj/JobForge/docs/architecture-overview.md)
- [docs/decisions/003-grounded-resume-evidence-pipeline.md](/home/leon/Documents/proj/JobForge/docs/decisions/003-grounded-resume-evidence-pipeline.md)
- [docs/decisions/004-user-resume-evidence-root-and-projects-milestone.md](/home/leon/Documents/proj/JobForge/docs/decisions/004-user-resume-evidence-root-and-projects-milestone.md)
- [docs/decisions/005-subsystem-package-organization.md](/home/leon/Documents/proj/JobForge/docs/decisions/005-subsystem-package-organization.md)
- [docs/decisions/008-standalone-resume-evidence-and-generation-layers.md](/home/leon/Documents/proj/JobForge/docs/decisions/008-standalone-resume-evidence-and-generation-layers.md)

## Current Limitations

- JobForge does not yet ship a public full-resume generation API.
- The evidence layer currently stops at `projects.yaml` and `skills.yaml`.
- Resume synthesis, assembly, and additional evidence files are still future work.
