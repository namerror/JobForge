# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Runtime selection configuration is now subsystem-scoped: use `SKILL_METHOD`, `SKILL_TOP_N`, `SKILL_BASELINE_FILTER`, `PROJ_METHOD`, and `PROJ_TOP_N` instead of generic selection env vars.
- Skill-selection and project-selection LLM defaults are configured separately with `SKILL_LLM_*` and `PROJ_LLM_*` settings; legacy `LLM_MODEL` and `LLM_MAX_OUTPUT_TOKENS` are no longer read.
- `/health` now reports scoped `skill_selection` and `project_selection` config blocks instead of top-level generic selection keys.

## [0.2.0] - 2026-04-27

### Added
- `POST /select-projects` project-selection API with baseline/LLM methods, local validation, baseline fallback, and project-selection metrics
- `app/skill_selection/` subsystem package for skill-selection models, scoring, clients, data, and compatibility shims for legacy import paths
- Interactive projects evidence CLI with staged in-memory CRUD, hidden auto-generated IDs, and explicit `apply` confirmation before writing `user/resume_evidence/projects.yaml`
- Optional `baseline_filter` request/config flag that pre-filters deterministic baseline matches before embeddings or LLM scoring, with full-baseline fallback behavior
- `/metrics-lite` now reports cumulative model token usage and counts fallback responses under the effective baseline method
- LLM skill-selection method (`method="llm"`) with OpenAI Responses API scoring, strict local validation, deterministic ranking, dev metadata, and baseline fallback
- Embeddings scorer (`embedding_select_skills`) in `app/skill_selection/scoring/embeddings.py` with per-category cosine similarity ranking, stable tie-breaking, dev mode similarity scores, short role text warnings, and rate limit error handling
- Role family detection and inheritance in baseline scorer
- Baseline scoring algorithm with role-specific boosts
- Skill selection service with latency tracking and structured logging
- `include_zero` option in skill ranking to include irrelevant skills for evaluation purposes, defaulting to False

### Fixed
- Empty string handling in baseline scorer to prevent false partial matches
- TOP_N environment variable type conversion (string to int)
- Attribute name mismatch in `baseline_select_skills()` (job_role vs role)
- Embedding truncation logging now uses standard logging extras
- `embed_role` honors `EMBEDDING_DIMENSIONS` for consistent embedding sizes
- `embed_skills` now validates against empty input batches

## [0.1.0] - Initial Setup

### Added
- Basic FastAPI application structure
- Baseline scoring algorithm with synonym normalization
- Role profile definitions for multiple engineering roles
- Health check endpoint
- Select skills endpoint (placeholder implementation)
