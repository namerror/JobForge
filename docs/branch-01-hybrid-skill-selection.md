# Branch 01: Hybrid Skill Selection

## Purpose
This branch is the next skill-selection upgrade. It stays within the current skill-selector service and does not start resume generation work yet.

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
- Keep the current `/select-skills` request/response contract unchanged for v1 hybrid work.
- Score every candidate skill with both baseline and embeddings when embeddings are available.
- Normalize baseline scores from raw `0/1/3` to `0.0`, `0.33`, and `1.0`.
- Compute `hybrid_score = 0.6 * baseline_norm + 0.4 * embedding_similarity`.
- Rank deterministically by `hybrid_score desc`, then normalized skill name asc.
- If embeddings fail, fall back to pure baseline and surface a warning in dev metadata.
- Reuse current synonym normalization, role profiles, embedding cache, and eval datasets rather than introducing branch-specific copies.

## Quick Guide
1. Add `hybrid` dispatch in `app/services/skill_selector.py` and `scripts/eval.py`.
2. Implement score fusion in a dedicated scorer without changing the public API shape.
3. Reuse current normalization and cache behavior before adding any hybrid-specific heuristics.
4. Benchmark against existing eval cases before tuning weights.
5. Only tune weights after baseline-vs-embedding-vs-hybrid comparisons are saved.

## Interfaces And Resources
- Input and output stay aligned with the current endpoint:

```json
{
  "job_role": "AI/ML Engineer",
  "job_text": "Optional job description text",
  "technology": ["Docker", "AWS", "TensorFlow"],
  "programming": ["Python", "SQL"],
  "concepts": ["Machine Learning", "CI/CD"],
  "top_n": 5,
  "method": "hybrid",
  "dev_mode": true
}
```

- Dev metadata may include per-skill baseline score, embedding similarity, fused score, normalized skill, and fallback warnings.
- Reuse these existing resources directly:
  - `app/scoring/baseline.py`
  - `app/scoring/embeddings.py`
  - `app/services/embedding_client.py`
  - `app/services/embedding_cache.py`
- Treat `data/eval_runs/` as a future convention for saved benchmark outputs; create it only when benchmark persistence is implemented.

## Benchmarking And Verification
- Compare `baseline`, `embeddings`, and `hybrid` on the same eval cases and metric keys.
- Preserve current subset guarantees and deterministic ordering in tests.
- Add hybrid-specific checks for:
  - embedding failure fallback
  - deterministic tie-breaking
  - score fusion correctness
  - unchanged API response shape
- Record both quality metrics and efficiency metrics so weight tuning is evidence-driven rather than anecdotal.

