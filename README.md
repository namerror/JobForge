# Skill Relevance Selector (FastAPI Microservice)

A small FastAPI microservice that selects and ranks the most relevant skills for a given job role.
It is designed for resume generation pipelines and prioritizes determinism, testability, and extensibility.

## What this service does (and does not do)

### ✅ Does
- Accepts:
  - `job_role` (required): whatever title the job poster provides (e.g. "AI/ML Engineer", "Frontend Developer", "Data Scientist")
  - `job_text` (optional): job description or other context to help with selection
  - categorized user skills in 3 buckets:
    - `technology`: specific tools, frameworks, platforms (e.g. "Docker", "AWS", "TensorFlow")
    - `programming`: programming languages (e.g. "Python", "Java", "SQL")
    - `concepts`: broader technical concepts, methodologies, or domains (e.g. "Machine Learning", "CI/CD", "Distributed Systems")
  - `top_n` (optional): number of top skills to return per category (default: 5)
  - `method` (optional): selection method
- Returns:
  - the most relevant skills per category (ranked, stable ordering, ties allowed)
  - debug details (similarity scores, normalized skill names) when `DEV_MODE=true`
- Supports multiple methods (config-driven):
  - `baseline` (deterministic keyword/role-profile scoring)
  - `embeddings` (cosine similarity ranking using OpenAI embeddings)
  - `hybrid` (currently in development, combines both approaches for improved accuracy)
  - `llm` (OpenAI Responses API scoring with local validation, ranking, and baseline fallback)

### ❌ Does not
- Invent skills not present in the input
- Infer seniority, domain, or user background
- Generate resume bullets (this service is only selection + ranking)

---

## API

### Health
`GET /health`

Response:
```json
{ 
  "status": "ok",
  "version": "version_info_here",
  "method": "your_method_here",
  "top_n": top_n_skills_returned,
  "dev_mode": true_or_false
}
```

### Select Skills
`POST /select_skills`

Request:
```json
{
  "job_role": "AI/ML Engineer",
  "job_description": "Optional text...",
  "technology": ["Docker", "Kubernetes", "AWS", "PostgreSQL", "TensorFlow"],
  "programming": ["Python", "TypeScript", "SQL"],
  "concepts": ["Machine Learning", "CI/CD", "Distributed Systems"]
}
```

Response (example):
```json
{
  "technology": ["TensorFlow", "AWS", "Docker"],
  "programming": ["Python"],
  "concepts": ["Machine Learning", "Distributed Systems"],
  "details": {
    ...
  }
}
```

### Logging Metrics
`POST /metrics-lite`
Response:
```json
{
  "requests_total": total_requests,
  "errors_total": total_errors,
  "avg_latency_ms": average_latency_in_ms,
  "method_usage": method_usage,
}
```

## Configuration

The service can be configured via environment variables or a config file to specify:
```
METHOD=your_method_here # e.g., baseline, embeddings, llm
DEV_MODE="true" # Enable verbose logging and mock data for development
TOP_N=your_number_here # Number of top skills to return per category
LOG_LEVEL=your_log_level_here # e.g., DEBUG, INFO, WARNING

OPENAI_API_KEY=your_openai_api_key_here # Required for embeddings and llm methods

EMBEDDING_MODEL=your_embedding_model_here # e.g., text-embedding-3-small
EMBEDDING_BATCH_SIZE=your_batch_size_here # e.g., 100
EMBEDDING_DIMENSIONS=your_embedding_dimensions_here # optional, remove if not needed

LLM_MODEL=your_llm_model_here # e.g., gpt-5-mini
LLM_MAX_OUTPUT_TOKENS=1200
```

## Running Locally

### Install Requirements
Ensure you have Python 3.10+ and pip installed, then run:
```bash
pip install -r requirements.txt
```

### Start the Service
```bash
uvicorn app.main:app --reload
```

---

## Running Tests

### Prerequisites
Tests require the venv to be active and `PYTHONPATH` set to the project root so that `app` is importable.

```bash
# Activate the virtual environment
source .venv/bin/activate
```

### Run All Tests
```bash
PYTHONPATH=. pytest
```

### Run a Specific File
```bash
PYTHONPATH=. pytest tests/test_baseline.py
```

### Run with Verbose Output
```bash
PYTHONPATH=. pytest -v
```

### Run a Single Test by Name
```bash
PYTHONPATH=. pytest -k "test_name_here"
```

### Notes
- `DEV_MODE=true` and `TOP_N=10` are set automatically by `tests/conftest.py` — no `.env` needed for tests.
- `tests/test_embeddings.py` may fail during active development of the embeddings scorer; skip it with `--ignore=tests/test_embeddings.py` if needed.
- Integration tests in `tests/test_integration.py` and `tests/test_health.py` exercise the full API stack and require `METHOD` to be set to a supported value (`baseline`, `embeddings`, or `llm`).
