### 2026-04-13 - Revise Branch 01 baseline filter plan

**Agent:** Codex (GPT-5)

**Changes:**
- `docs/branch-01-hybrid-skill-selection.md:1-6` - Renamed the branch concept to baseline-filtered skill selection and clarified that `method` remains the selected scorer while `baseline_filter` controls the optional pre-filter.
- `docs/branch-01-hybrid-skill-selection.md:31-48` - Replaced the previous score-fusion plan with the two-pass baseline-recognized/unrecognized flow, default behavior, merge rules, and deterministic ranking.
- `docs/branch-01-hybrid-skill-selection.md:50-77` - Updated the future request example and public interface notes to use `method: "embeddings"` plus `baseline_filter: true`.
- `docs/branch-01-hybrid-skill-selection.md:79-90` - Revised benchmark and verification guidance to compare methods with and without `baseline_filter`.

**Rationale:**
The planned approach no longer introduces a separate scoring method. The document now treats baseline filtering as an opt-in request/config flag that can improve model-backed scorers by allowing deterministic role-profile matches to be handled first while passing only unrecognized skills to the selected method.

**Tests:**
- Documentation-only verification: confirmed the Branch 01 plan now describes `baseline_filter`, keeps actual scorer names as method values, and includes a request example with `"baseline_filter": true`.
- No automated tests were run because no app code changed.

**Impact:**
Future implementation work can add the baseline-filtered flow without adding another method dispatch branch. The plan now preserves backward compatibility by making `baseline_filter` default to `false` and keeps benchmark guidance aligned with method-plus-flag comparisons.
