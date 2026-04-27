# Resume Engine

This project is evolving from a skill-selection microservice into a grounded resume-generation service. Today the repo ships two capability tracks:

- a production FastAPI API for skill selection with deterministic baseline, embeddings, and LLM methods
- a public project-selection API for ranking explicit user project candidates for a target job
- an implemented first milestone of the evidence-based resume pipeline centered on `user/resume_evidence/projects.yaml`

The app is now organized around peer subsystems under `app/`: `skill_selection`, `project_selection`, and `resume_evidence`.

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

The first implemented milestone is the `app.resume_evidence` package.

- `app/resume_evidence/models.py`
  - strict Pydantic models for `projects.yaml`
- `app/resume_evidence/loader.py`
  - schema registry and deterministic YAML loading
- `app/resume_evidence/session.py`
  - staged in-memory CRUD with validation-before-mutation and atomic apply-to-disk writes
- `app/resume_evidence/cli.py`
  - interactive project-evidence CLI
- `app/main.py`
  - loads registered evidence on startup into `app.state.resume_evidence`

The currently implemented evidence schema is:

- `user/resume_evidence/projects.yaml`
  - `schema_version: 1`
  - strict project records with `id`, `name`, `summary`, `highlights`, `active`, `skills`, and optional `links`

### Project selection API

The project-selection subsystem ranks explicit project candidates for a job target without generating resume prose.

- `POST /select-projects`
  - accepts `context` with job title/description and explicit project `candidates`
  - supports deterministic `baseline` and model-backed `llm` methods
  - validates LLM project-id scores locally and falls back to baseline when needed
  - returns project IDs and scores, not project summaries, highlights, links, or generated claims

### Evidence CLI workflow

Use the CLI to manage staged edits to `projects.yaml` without hand-editing YAML:

```bash
PYTHONPATH=. python -m app.resume_evidence.cli
```

If your shell does not expose `python`, run:

```bash
PYTHONPATH=. python3 -m app.resume_evidence.cli
```

Available commands:

- `list`
- `show <index>`
- `create`
- `edit <index>`
- `delete <index>`
- `apply`
- `reload`
- `quit`

The CLI keeps edits staged in memory until `apply` is confirmed, preserves stable hidden IDs, and writes atomically to disk.

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
- the resume-evidence package establishes grounded source-of-truth data under `user/resume_evidence/`
- future synthesis will combine target job context, evidence, and selected skills into structured fill data
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
  "method": "baseline",
  "top_n": 10,
  "baseline_filter": false,
  "dev_mode": true
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
METHOD=baseline # available options: baseline, embeddings, llm
TOP_N=10 # how many top-ranked skills to return per category
BASELINE_FILTER=false # if true, deterministic matches bypass model-backed scoring and are guaranteed in the output
DEV_MODE=true # return debugging info
LOG_LEVEL=INFO

OPENAI_API_KEY=your_key_here

EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_BATCH_SIZE=100

LLM_MODEL=gpt-5-mini
LLM_MAX_OUTPUT_TOKENS=1200
```

`OPENAI_API_KEY` is only required for skill-selection `embeddings`, skill-selection `llm`, and project-selection `llm` requests.

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
PYTHONPATH=. python -m app.resume_evidence.cli
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

The following pieces are planned but not yet implemented as a public resume-generation flow:

- additional evidence files under `user/resume_evidence/`
  - `profile.yaml`
  - `experience.yaml`
  - `skills.yaml`
- a rebuildable runtime evidence index spanning more than `projects.yaml`
- grounded synthesis/extraction that returns structured resume fill data with provenance
- resume format definitions under `app/data/resume_formats/`
- deterministic assembly that renders full resume artifacts from structured fill data

See:

- [docs/branch-03-grounded-resume-generation.md](/home/leon/Documents/proj/JobForge/docs/branch-03-grounded-resume-generation.md)
- [docs/architecture-overview.md](/home/leon/Documents/proj/JobForge/docs/architecture-overview.md)
- [docs/decisions/003-grounded-resume-evidence-pipeline.md](/home/leon/Documents/proj/JobForge/docs/decisions/003-grounded-resume-evidence-pipeline.md)
- [docs/decisions/004-user-resume-evidence-root-and-projects-milestone.md](/home/leon/Documents/proj/JobForge/docs/decisions/004-user-resume-evidence-root-and-projects-milestone.md)
- [docs/decisions/005-subsystem-package-organization.md](/home/leon/Documents/proj/JobForge/docs/decisions/005-subsystem-package-organization.md)

## Current Limitations

- JobForge does not yet ship a public full-resume generation API.
- `projects.yaml` is the only implemented evidence schema today.
- Resume synthesis, assembly, and additional evidence files are still future work.
