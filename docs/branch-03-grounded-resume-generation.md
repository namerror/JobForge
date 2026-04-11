# Branch 03: Grounded Resume Generation

## Purpose
This branch is the first expansion beyond skill selection. Its first milestone is evidence extraction plus grounded synthesis into a structured resume draft schema, not polished free-form resume generation.

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
- Define a future-facing resume pipeline built around extraction and grounded synthesis, not free-form generation first.
- Introduce two core inputs:
  - `job_target` with `job_title` and `job_description`
  - `user_profile` with structured evidence items carrying stable `id` values
- Introduce a structured resume draft output where every generated claim or highlight includes `evidence_ids`.
- Enforce hard grounding rules:
  - no claim may appear without user-profile evidence
  - the job description may guide prioritization, but it is never evidence of user experience
  - unsupported claims must be omitted, not guessed
- Treat skill selection as one input signal for resume drafting, not the entire source of truth.

## Quick Guide
1. Define the user profile evidence schema first.
2. Define the grounded resume draft schema second.
3. Connect skill selection output as one prioritization signal, not the whole system.
4. Build evaluation around factual support, relevance, compression quality, and token efficiency.
5. Defer polished prose generation until the extraction and grounding layers benchmark well.

## Interfaces And Resources
- This branch introduces a future-facing schema. It does not change the current production `/select-skills` contract until separate implementation work is approved.
- Planned input shape:

```json
{
  "job_target": {
    "job_title": "Senior Backend Engineer",
    "job_description": "Build scalable APIs and distributed systems."
  },
  "user_profile": {
    "evidence_items": [
      {
        "id": "exp_001",
        "type": "experience",
        "source": "work_history",
        "text": "Built and maintained Python APIs serving internal teams."
      },
      {
        "id": "skill_014",
        "type": "skill",
        "source": "profile_skills",
        "text": "Python"
      }
    ]
  }
}
```

- Planned output shape:

```json
{
  "summary": [
    {
      "text": "Backend engineer with API and Python experience.",
      "evidence_ids": ["exp_001", "skill_014"]
    }
  ],
  "selected_skills": {
    "technology": ["Docker"],
    "programming": ["Python"],
    "concepts": ["API Design"]
  },
  "warnings": []
}
```

- Shared existing resources still matter here:
  - `app/models.py`
  - `app/services/skill_selector.py`
  - `app/scoring/*`
  - `data/eval_cases/*.json`
- Treat `data/eval_runs/` as a future convention for saved benchmark outputs, and treat any resume-specific fixtures as future additions rather than existing repository assets.

## Benchmarking And Verification
- Build a benchmark plan that scores:
  - factual support and evidence coverage
  - relevance to the target job
  - compression quality
  - omission of unsupported claims
  - token and latency efficiency
- Add checks that every generated statement can be traced back to one or more evidence IDs.
- Keep the first milestone structured and inspectable so failures are easy to diagnose before prose generation is attempted.
- Do not score this branch only on fluency; factual grounding and supportability are the primary quality gates.

