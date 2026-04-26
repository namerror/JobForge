# Branch 03: Project Selection Plan

## Purpose

This milestone adds the first internal project-ranking layer for the grounded resume evidence pipeline. It selects user-provided project candidates for a job target without generating resume prose or changing evidence files.

## Summary

- Implement an internal project selector only: no FastAPI route, no CLI command, no public API change.
- Accept explicit project candidates with `id`, `name`, `summary`, and categorized `skills`, plus job context `title` and `description`.
- Support `method="llm"` and `method="baseline"`.
- Validate LLM scores locally and fall back to deterministic baseline scoring on client or response failure.

## Components

- `app/project_selection/models.py`
  - Defines `ProjectJobContext`, `ProjectCandidate`, `RankedProject`, and `ProjectSelectionResult`.
  - Reuses `ProjectSkills` so project skill categories remain exactly `technology`, `programming`, and `concepts`.
- `app/project_selection/baseline.py`
  - Scores each project with existing baseline skill selection over project skills.
  - Blends top skill matches with deterministic project-summary/job-context token overlap.
- `app/project_selection/llm.py`
  - Calls a dedicated project LLM client, validates returned project-id scores, ranks locally, and falls back to baseline when the LLM path is unusable.
- `app/project_selection/selector.py`
  - Exposes `select_projects(...)` as the service-style internal entrypoint.
- `app/services/project_llm_client.py`
  - Owns the OpenAI Responses API call for project scoring.

## Scoring Behavior

Baseline scoring:

- Runs `baseline_select_skills()` against each project’s categorized skills using job title and description.
- Computes `skill_score` from the strongest non-zero baseline skill matches: sort raw scores descending, take top 5, and normalize by `3 * number_of_considered_skills`.
- Computes `text_overlap_score` from deterministic token coverage between project summary and job title + description, ignoring a fixed stopword set.
- Computes final score as `0.75 * skill_score + 0.25 * text_overlap_score`.
- Ranks by final score desc, matched skill count desc, text overlap desc, normalized project name asc, project id asc.

LLM scoring:

- Sends compact JSON containing job context and project candidates.
- Requires strict JSON shaped as project ID to integer score `0..3`.
- Discards invented IDs and invalid scores, performs final ranking locally, and normalizes scores with `score / 3.0`.
- Falls back to full baseline selection if the client fails or the response is too malformed to use.

## Tests And Verification

- Baseline tests cover skill-heavy ranking, top-match aggregation, deterministic tie-breaking, and empty input safety.
- LLM selector tests cover local ranking, invented IDs, invalid scores, fallback behavior, and token metadata.
- Client tests cover strict schema construction, compact payloads, model parameter compatibility, invalid JSON, and missing API keys.
- Service/model tests cover duplicate project IDs, `top_n` slicing after ranking, and output that contains project IDs/scores rather than generated project content.

## Assumptions

- Core selection uses only project `summary` and `skills`; `highlights`, `links`, and `active` are outside v1 scoring input.
- Callers are responsible for passing the candidate set they want ranked.
- Saved evidence adapters can be added later; v1 starts with explicit candidates for testability and reuse.
- This milestone does not update `docs/CHANGELOG.md` because it is internal and not user-facing.
