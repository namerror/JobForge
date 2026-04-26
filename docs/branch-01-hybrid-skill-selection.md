# Branch 01: Baseline-Filtered Skill Selection

## Purpose
This branch is the next skill-selection upgrade. It stays within the current skill-selector service and does not start resume generation work yet.

The approach is an optional two-pass selection flow controlled by `baseline_filter`. The request `method` still names the scorer to use, such as `baseline`, `embeddings`, or `llm`; `baseline_filter` only controls whether the deterministic baseline scorer pre-filters recognized skills before the selected method handles the remainder.

## Current Repo Context
- The current production request/response contract is `SkillSelectRequest` and `SkillSelectResponse` in `app/skill_selection/models.py`.
- Implemented methods today are `baseline`, `embeddings` and `llm`; service dispatch lives in `app/skill_selection/selector.py`.
- Baseline ranking is deterministic and remains the required fallback.
- Evaluation assets already exist in `data/eval_cases/` and `scripts/eval.py`.

## Shared Contract
- Canonical skill categories remain exactly: `technology`, `programming`, `concepts`.
- Skill-selection outputs must always be a strict subset of the user-provided skills for the same category.
- Baseline remains the safe fallback path and must keep working if embeddings or LLM-based methods fail.
- All public JSON examples use snake_case and match the existing `/select-skills` shape unless a doc explicitly introduces a future schema.
- Shared source-of-truth resources:
  - role profiles: `app/skill_selection/data/role_profiles/*.yaml`
  - skill normalization: `app/skill_selection/scoring/synonyms.py`
  - normalized skill pools: `data/skill_pools/normalized/skill_pools.json`
  - evaluation cases: `data/eval_cases/*.json`
  - embedding cache: `app/skill_selection/data/embeddings/{model}/`
- Model-backed branches use the existing OpenAI Python SDK direction and must route outbound calls through one service/client layer, not scattered direct calls.
- Benchmarking must measure both quality and efficiency:
  - quality: relevance, subset compliance, grounding/support, failure handling
  - efficiency: prompt/response token usage where applicable, API calls, cache hits, latency
- Any future saved benchmark outputs should use machine-readable JSON under `data/eval_runs/` and reuse comparable metric keys across branches.

## Branch-Specific Plan
- Add a future `baseline_filter` request/config option with default `false` so current method behavior is preserved unless callers opt in.
- When `baseline_filter=false`, dispatch directly to the selected `method` and keep existing method behavior unchanged.
- When `baseline_filter=true`, run the deterministic baseline scorer over all user-provided skills first.
- Treat skills with baseline score `> 0` as recognized because they matched the resolved role profile from `app/skill_selection/data/role_profiles/*.yaml`.
- Pass only unrecognized skills, baseline score `0`, to the selected non-baseline method for second-pass scoring.
- Merge baseline-recognized skills and second-pass-scored skills per category before taking `top_n`.
- Normalize all final candidate scores to a comparable `0.0` to `1.0` range before final ranking.
- Rank deterministically by normalized final score descending, then normalized skill name ascending.
- If the selected model-backed method fails, fall back safely without breaking the baseline path and surface a warning in dev metadata.
- For `method="baseline"`, `baseline_filter` is effectively a no-op because baseline already owns the full selection path.

## Quick Guide
1. Add `baseline_filter` to the future request/config surface; do not add a new scoring method.
2. Reuse baseline scoring and role profile knowledge to split recognized from unrecognized skills.
3. Reuse the selected method scorer only for the unrecognized remainder.
4. Merge the two scored candidate lists, normalize final scores, and apply deterministic ordering.
5. Benchmark each method with and without `baseline_filter` before tuning any score normalization behavior.

## Interfaces And Resources
- Input and output stay aligned with the current endpoint, with `baseline_filter` introduced as a future snake_case request field:

```json
{
  "job_role": "AI/ML Engineer",
  "job_text": "Optional job description text",
  "technology": ["Docker", "AWS", "TensorFlow"],
  "programming": ["Python", "SQL"],
  "concepts": ["Machine Learning", "CI/CD"],
  "top_n": 5,
  "method": "embeddings",
  "baseline_filter": true,
  "dev_mode": true
}
```

- Future public request field: `baseline_filter: bool | None = None`.
- JSON key: `"baseline_filter"`.
- Default behavior: `false`.
- Future method values remain actual scorers only: `baseline`, `embeddings`, `llm`.
- Dev metadata may include baseline-recognized versus second-pass source, baseline raw score, selected method score or similarity, normalized final score, normalized skill, and fallback warnings.
- Reuse these existing resources directly:
  - `app/skill_selection/scoring/baseline.py`
  - `app/skill_selection/scoring/embeddings.py`
  - `app/skill_selection/embedding_client.py`
  - `app/skill_selection/embedding_cache.py`
- Treat `data/eval_runs/` as a future convention for saved benchmark outputs; create it only when benchmark persistence is implemented.

## Benchmarking And Verification
- Compare each method with and without `baseline_filter`, for example `embeddings` versus `embeddings + baseline_filter`.
- Preserve current subset guarantees and deterministic ordering in tests.
- Add baseline-filter checks for:
  - `baseline_filter=false` preserves existing method behavior
  - `baseline_filter=true` sends only baseline-unrecognized skills to the selected method
  - final output remains a strict subset of user-provided skills
  - deterministic tie-breaking after merging
  - selected method failure fallback
  - `method="baseline"` treats `baseline_filter` as a no-op
  - unchanged API response shape
- Record quality metrics and efficiency metrics, including latency, API-call count, cache hits, and token usage where applicable.
