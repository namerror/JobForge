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