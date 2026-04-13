# 002. Baseline Filter Selection

Date: 2026-04-13

## Status

Accepted

## Context

The service already supports `baseline`, `embeddings`, and `llm` skill-selection methods. Branch 01 needs a way to let deterministic role-profile matches be handled before model-backed scoring without adding a new public method or weakening the baseline fallback invariant.

## Decision

Add `baseline_filter` as an optional request field and `BASELINE_FILTER` as an environment setting. Request values override the setting, matching `method`, `top_n`, and `dev_mode`.

When enabled for `embeddings` or `llm`, the service runs baseline scoring first with zero-score details included, treats baseline score `> 0` as recognized, sends only zero-score skills to the requested model-backed scorer, merges all scored candidates, normalizes scores to `0.0..1.0`, and applies deterministic final ranking.

Normalization is intentionally simple:
- Baseline score: `score / 3`
- LLM score: `score / 3`
- Embedding similarity: clamped to `0.0..1.0`

If the second-pass scorer raises or reports fallback metadata, the service returns a full baseline selection over the original input and marks `_fallback_method: "baseline"` in internal metadata.

## Consequences

### Positive
- Keeps public `method` values limited to actual scorers.
- Preserves default behavior unless callers opt in.
- Reduces model-backed scorer work by filtering known role-profile matches first.
- Keeps metrics aligned with effective fallback behavior.

### Negative
- Adds service orchestration complexity and internal metadata merging.
- Simple score normalization is easy to test but may need benchmark-driven tuning later.

### Neutral
- `method="baseline"` ignores `baseline_filter` because baseline already owns the full path.
- Benchmark output records whether baseline filtering was enabled for comparability.

## Alternatives Considered

- Add a new `hybrid` method: rejected because it would blur method identity and conflict with the Branch 01 contract.
- Return only baseline-recognized skills on second-pass failure: rejected because full baseline fallback is safer and more consistent with existing model-backed fallback behavior.
- Use rank-percentile or source-priority normalization: deferred until evaluation data shows simple per-method normalization is insufficient.
