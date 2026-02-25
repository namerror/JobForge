# Architecture Overview

This document maps `app/` relationships and runtime logic flow so agents can navigate the codebase quickly.

## 1) High-Level Structure (`app/`)

- `app/main.py`: FastAPI app composition, lifespan setup, HTTP routes.
- `app/models.py`: Request/response contracts (`SkillSelectRequest`, `SkillSelectResponse`).
- `app/config.py`: Runtime settings (`METHOD`, `TOP_N`, `DEV_MODE`, `LOG_LEVEL`) from env.
- `app/services/skill_selector.py`: Service orchestration for method selection, metrics, logging.
- `app/scoring/baseline.py`: Deterministic baseline ranking pipeline.
- `app/scoring/role_profiles.py`: Role profile loading and role-family detection.
- `app/scoring/synonyms.py`: Skill normalization alias map.
- `app/metrics.py`: In-memory thread-safe counters/latency aggregation.
- `app/logging_config.py`: JSON logger formatter and root logger setup.
- `app/data/role_profiles/*.yaml`: Role profile keyword knowledge base.

## 2) Module Dependency Map

```text
app.main
  -> app.models
  -> app.config
  -> app.services.skill_selector
  -> app.metrics
  -> app.logging_config

app.services.skill_selector
  -> app.config
  -> app.metrics
  -> app.models
  -> app.scoring.baseline

app.scoring.baseline
  -> app.scoring.synonyms
  -> app.scoring.role_profiles (detect_role_family + ROLE_PROFILES)

app.scoring.role_profiles
  -> app/data/role_profiles/*.yaml
```

## 3) End-to-End Request Flow

```mermaid
flowchart TD
    A[POST /select-skills] --> B[FastAPI validates payload into SkillSelectRequest]
    B --> C[main.select_skills]
    C --> D[services.select_skills_service]
    D --> E[Resolve method/top_n/dev_mode from request override or settings]
    E --> F[metrics.inc_request - method]
    F --> G{method == baseline?}
    G -- no --> H[raise ValueError Unsupported METHOD]
    G -- yes --> I[baseline_select_skills]
    I --> J[detect_role_family - job_role]
    J --> K[rank category: technology/programming/concepts]
    K --> L[score_skill - normalize_skill - synonym lookup]
    L --> M[ROLE_PROFILES keyword match scoring]
    M --> N[sort by score desc then skill asc]
    N --> O[top_n slice per category]
    O --> P[build meta details if dev_mode]
    P --> Q[metrics.observe_latency_ms]
    Q --> R[structured log event]
    R --> S[SkillSelectResponse]
    H --> T[metrics.inc_error + exception log]
```

## 4) Baseline Scoring Logic Flow

`baseline_select_skills(...)` processes each category independently with shared rules:

1. Role family resolution:
- `detect_role_family(job_role)` converts role string to a profile key candidate.

2. Skill normalization:
- `normalize_skill(skill)` lowercases/trims and canonicalizes aliases via `SYNONYM_TO_NORMALIZED`.

3. Keyword matching:
- Loads category keywords from `ROLE_PROFILES[role_family]` (fallback to `general`).
- If profile declares `inherits`, inherited keywords are merged for that category.

4. Score assignment:
- Exact canonical keyword match => `3.0`
- Partial containment match => `1.0`
- Otherwise => `0.0` (excluded unless `include_zero=True`)

5. Deterministic ranking:
- Sort key: `(-score, original_skill_string)`
- Stable top selection: first `top_n` skills

6. Response shaping:
- Returns selected skills per category.
- Returns per-skill details only when `dev_mode=True`.

## 5) Data Flow and State

- Configuration state:
  - Source: `.env` + defaults in `app/config.py`.
  - Read at runtime for fallback behavior.

- Knowledge state:
  - Role profiles loaded from YAML at module import time in `role_profiles.py`.
  - Synonym map loaded from static dict in `synonyms.py`.

- Runtime mutable state:
  - `metrics` singleton in `app/metrics.py` (protected by lock).

## 6) Route Responsibilities

- `GET /health`:
  - Liveness + effective config surface (`method`, `top_n`, `dev_mode`).

- `GET /metrics-lite`:
  - In-memory counters and average latency snapshot.

- `POST /select-skills`:
  - Main business route; delegates to service layer and converts `ValueError` to HTTP 400.

## 7) Extension Points (Safe Order)

1. Add/adjust role profile YAML keywords in `app/data/role_profiles/`.
2. Add/adjust synonyms in `app/scoring/synonyms.py`.
3. Extend service method dispatch in `app/services/skill_selector.py` for new methods.
4. Keep baseline path intact as deterministic fallback.

## 8) Agent Quick-Read Sequence

1. `AGENTS.md` (repo constraints and logging requirements).
2. `CLAUDE.md` (service-specific engineering rules).
3. `docs/architecture-overview.md` (this file; relationships + flow).
4. `app/main.py` -> `app/services/skill_selector.py` -> `app/scoring/baseline.py`.
5. `app/scoring/role_profiles.py` + `app/data/role_profiles/*.yaml`.
