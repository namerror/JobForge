# Branch 02: LLM Skill Selection

## Purpose
This branch explores a pure LLM-based skill-selection method while staying strictly within skill selection. It does not generate resume bullets, experience claims, or user profile content.

## Current Repo Context
- The current production request/response contract is `SkillSelectRequest` and `SkillSelectResponse` in `app/models.py`.
- Implemented methods today are `baseline` and `embeddings`; service dispatch lives in `app/services/skill_selector.py`.
- Baseline ranking is deterministic and remains the required fallback.
- Evaluation assets already exist in `data/eval_cases/` and `scripts/eval.py`.

## Shared Contract
- Canonical skill categories remain exactly: `technology`, `programming`, `concepts`.
- Skill-selection outputs must always be a strict subset of the user-provided skills for the same category.
- Baseline remains the safe fallback path and must keep working if embeddings or LLM-based methods fail.
- All public JSON examples use snake_case and match the existing `/select-skills` shape unless a doc explicitly introduces a future schema.
- Shared source-of-truth resources:
  - role profiles: `app/data/role_profiles/*.yaml`
  - skill normalization: `app/scoring/synonyms.py`
  - normalized skill pools: `data/skill_pools/normalized/skill_pools.json`
  - evaluation cases: `data/eval_cases/*.json`
  - embedding cache: `app/data/embeddings/{model}/`
- Model-backed branches use the existing OpenAI Python SDK direction and must route outbound calls through one service/client layer, not scattered direct calls.
- Benchmarking must measure both quality and efficiency:
  - quality: relevance, subset compliance, grounding/support, failure handling
  - efficiency: prompt/response token usage where applicable, API calls, cache hits, latency
- Any future saved benchmark outputs should use machine-readable JSON under `data/eval_runs/` and reuse comparable metric keys across branches.

## Branch-Specific Plan
- Lock v1 to OpenAI-only and use one dedicated LLM client wrapper rather than direct calls from scorers or routes.
- Use one fixed prompt template and deterministic model settings.
- The LLM must return structured JSON scoring every candidate skill; it must not return a free-form ranked list.
- Validate the model output strictly, drop any unknown or invented skills, and perform final ranking locally.
- Keep top-`N` slicing local to the server.
- If the LLM call fails or returns unusable output, fall back to the baseline method and surface a warning in dev metadata.

## Quick Guide
1. Add a dedicated LLM client wrapper under the service layer.
2. Define the prompt input schema and structured JSON output schema.
3. Implement strict validation and repair rules before ranking.
4. Sort locally by `score desc`, then normalized skill name asc.
5. Benchmark quality against baseline and hybrid while also logging token and latency cost.

## Interfaces And Resources
- Input and output stay aligned with the current endpoint:

```json
{
  "job_role": "Frontend Engineer",
  "job_text": "Optional job description text",
  "technology": ["React", "Vue", "Angular"],
  "programming": ["JavaScript", "TypeScript", "CSS"],
  "concepts": ["UI", "UX", "State Management"],
  "top_n": 5,
  "method": "llm",
  "dev_mode": true
}
```

- Expected model response shape for v1 should be structured JSON similar to:

```json
{
  "technology": {
    "React": 3,
    "Vue": 2,
    "Angular": 2
  },
  "programming": {
    "JavaScript": 3,
    "TypeScript": 3,
    "CSS": 2
  },
  "concepts": {
    "UI": 3,
    "UX": 3,
    "State Management": 2
  }
}
```

- Server-side ranking rule:
  - sort by score desc
  - tie-break by normalized skill name asc
  - slice top `N` after validation
- Reuse current normalization and evaluation resources; do not create an LLM-only dataset format.
- Treat `data/eval_runs/` as a future convention for saved benchmark outputs; create it only when benchmark persistence is implemented.

## Benchmarking And Verification
- Measure quality against the same eval cases used by baseline, embeddings, and hybrid.
- Track efficiency per request: prompt tokens, completion tokens, total tokens, API call count, and latency.
- Add validation tests for:
  - invented skills being discarded
  - malformed JSON repair/rejection paths
  - deterministic local ranking
  - fallback to baseline on client or parsing failure
- Keep this branch scoped to skill selection only; resume generation belongs to Branch 03.

