# Skill Relevance Selector (FastAPI Microservice)

A small FastAPI microservice that selects and ranks the most relevant skills for a given job role.
It is designed for resume generation pipelines and prioritizes determinism, testability, and extensibility.

## What this service does (and does not do)

### ✅ Does
- Accepts:
  - `job_role` (required)
  - `job_description` (optional)
  - categorized user skills in 3 buckets:
    - `Technology`
    - `Programming`
    - `Concepts`
- Returns:
  - the most relevant skills per category (ranked, stable ordering, ties allowed)
- Supports multiple methods (config-driven):
  - `baseline` (deterministic keyword/role-profile scoring)
  - `embeddings` (optional upgrade)
  - `hybrid` (baseline shortlist → embedding rerank)

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
{ "status": "ok" }
```

### Select Skills
Request:
```json
{
  "job_role": "AI/ML Engineer",
  "job_description": "Optional text...",
  "skills": {
    "Technology": ["Docker", "Kubernetes", "AWS", "PostgreSQL", "TensorFlow"],
    "Programming": ["Python", "TypeScript", "SQL"],
    "Concepts": ["Machine Learning", "CI/CD", "Distributed Systems"]
  }
}
```
Response (example):
```json
{
  "Technology": ["TensorFlow", "AWS", "Docker"],
  "Programming": ["Python"],
  "Concepts": ["Machine Learning", "Distributed Systems"]
}
```

---
## Configuration

The service can be configured via environment variables or a config file to specify:
```
METHOD=your_method_here # e.g., baseline, embeddings, hybrid
DEV_MODE="true" # Enable verbose logging and mock data for development
TOP_N=your_number_here # Number of top skills to return per category
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