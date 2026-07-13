# Resume Generation Token Efficiency Audit

Date: 2026-07-13

## Scope

This audit reviews the current resume generation pipeline for token efficiency,
cache reuse, fallback behavior, and design controls that affect repeated LLM
work. It is based on:

- `resume_generation/` orchestration code
- `app/*_selection`, `app/bulletpoints_generation`, and `app/link_scanning`
- current user config and evidence under `user/resume_generation/` and
  `user/resume_evidence/`
- current run artifacts:
  - `user/resume_generation/resume_run_manifest.json`
  - `user/resume_generation/resume_result.json`
  - `user/resume_generation/cache/skill_selection/*`
  - `user/resume_generation/cache/project_selection/*`
  - bullet-generation cache entries
- prior manual/agentic note:
  - `docs/notes/07-08-2026-Codex-resume-generation-agentic-test.md`

No code changes were made for this audit.

## Current Token Profile

The current manifest reports 21,151 successful response tokens across 12 API
calls. Bullet generation dominates the run:

- Project selection: 1 call, 1,920 tokens
- Project bullets: 5 calls, 9,086 tokens
- Experience bullets: 6 calls, 10,145 tokens
- Skill selection: recorded as 0 tokens because the LLM path failed and fell
  back to baseline before usable LLM metadata was preserved

Project and experience bullets therefore account for about 91% of recorded
successful token usage. The actual cost is higher when failed/truncated calls
are included.

## Ranked Findings

### 1. Skill LLM failure is cached as a successful fallback

**Severity:** High

The current skill selection cache entry records a fallback to baseline because
the LLM response was invalid JSON:

`LLM response was not valid JSON: Unterminated string starting at: line 20 column 5`

The request used `llm_max_output_tokens: 1200` and asked the LLM to score 42
skills. The skill LLM schema requires a score for every candidate skill, so a
1200-token cap is likely too small. Unlike bullet generation, skill selection
has no retry path with a larger output budget.

The fallback result is then cached as the stage result. Future runs can reuse a
degraded baseline result without retrying the LLM unless the cache key changes
or `force_refresh` is enabled.

**Why this matters:**

- Token spend from failed LLM calls is hidden.
- A transient/truncation failure becomes durable cached state.
- Resume quality drops because the fallback baseline is weak for the current
  target.

**Recommended design changes:**

- Add LLM response retry for skill selection on empty output, truncated JSON, or
  parse failure, using a larger computed output cap.
- Compute default `llm_max_output_tokens` from candidate count and schema size
  instead of a fixed global value.
- Preserve failed attempt usage metadata when possible.
- Mark cached entries with a quality/source state such as `llm_success`,
  `fallback_success`, or `degraded_fallback`.
- Consider not caching degraded fallback responses by default, or add a short
  TTL / explicit `cache_fallbacks` control.

### 2. Baseline fallback has role-profile weaknesses that explain poor skills

**Severity:** High

The current fallback selected broad distractors such as `C`, `C#`, `Java`,
`PyTorch`, `TensorFlow`, and `Deep Learning`, while missing target-relevant
items such as `FastAPI`, `RestAPI`, `Caching`, and `Database Management`.

Two implementation details explain this:

- Role detection uses only `job_role`, not the job description. The target title
  `Python Developer - Fully Remote` falls to `general` rather than a backend or
  API-focused profile.
- Role-profile inheritance is shallow. `general` inherits `fullstack`, but
  `fullstack` only contains empty direct keyword lists and itself inherits
  backend/frontend/devops. Because inheritance is not recursive, backend
  keywords such as `fastapi`, `api`, `rest api`, `caching`, and `database
  management` are not included through `general -> fullstack -> backend`.
- `general` directly inherits `ml/ai`, so ML terms are included even when the
  job is not ML-focused.

There is also a likely role key bug: `detect_role_family()` can return `ml`,
but the loaded profile key is `ml/ai`.

**Why this matters:**

When LLM selection fails, the system currently degrades to a fallback that is
not sufficiently job-aware. That makes fallback cheap but materially lower
quality.

**Recommended design changes:**

- Make profile inheritance recursive and tested.
- Fix the `ml` versus `ml/ai` role-key mismatch.
- Use job description text in baseline scoring. Exact job-description mentions
  should boost candidate skills such as `FastAPI`, `API`, `Docker`, `Linux`,
  `configuration`, and `local testing`.
- Add a role classifier for job text, not just title tokens.
- Split `general` into a conservative fallback that does not inherit ML by
  default.

### 3. Low-ranked projects are still fully bulletized

**Severity:** High

The current `project_selection.top_n` is `null`, so all ranked projects are
selected. In the current manifest, three projects have LLM score `1/3`, but all
three still receive full three-bullet generation calls:

- `2d-slam-robot`
- `hackproof-decentralized-reputation-system-for-hackers`
- `kim-1-trivia-game`

Those three low-fit project bullet calls cost 5,335 successful tokens in the
current run. They also make the final resume less targeted.

**Recommended design changes:**

- Set a default project `top_n` for resume generation, likely 2 or 3 for a
  one-page resume.
- Add a score threshold, e.g. skip project bullets below normalized score 0.5
  unless explicitly included.
- Support a `project_selection.include_below_threshold` override for manual
  experiments.
- Apply selection before link scanning and bullet generation so weak projects do
  not trigger later expensive stages.

### 4. Link scanning should become persistent evidence enrichment, not normal generation

**Severity:** High

The current project link scanning stage enriches selected projects in memory and
then passes the enriched record to bullet generation. It does not write scanned
highlights back to durable evidence. The stage is disabled in current config,
but if enabled it would run as part of the normal generation pass and use
`web_search`, which is likely the most expensive and least deterministic stage.

Experience records already have `links`, but there is no experience link
scanning orchestration or endpoint. Only project links are scanned today.

**Recommended design changes:**

- Split link scanning into an explicit enrichment command, separate from normal
  resume generation.
- Store accepted scan results back into evidence files, with provenance:
  `text`, `source_url`, `scanned_at`, `link_digest`, `scanner_model`, and
  possibly `accepted_by_user`.
- Support project and experience enrichment symmetrically.
- Add a scan policy:
  - `manual`: only scan when requested
  - `missing`: scan records with links but no scanned evidence
  - `stale`: scan only when link digest or scan age changes
  - `force`: rescan everything
- Keep the normal generation path as selection + bullet generation over already
  enriched evidence.

This matches the user-observed design direction: repository/codebase scanning
should be done once, or only when the user decides, not on every resume pass.

### 5. Cache keys include post-processing and debug fields

**Severity:** High

The stage cache keys exact outgoing request payloads. That means changes to
`top_n`, `dev_mode`, and `llm_max_output_tokens` can trigger new HTTP/LLM work.

For skill and project selection, `top_n` is applied locally after the LLM scores
all candidates. `dev_mode` controls details in responses and does not change
the LLM request. These fields are currently cache-key relevant because the cache
stores the endpoint response, not the raw reusable model result.

`llm_max_output_tokens` is more nuanced. It can affect truncation and success,
so it should not simply be ignored in every case. However, when a sufficient
token cap has already produced a complete raw result, changing the cap should
not necessarily force regeneration.

**Recommended design changes:**

- Introduce semantic cache layers:
  - raw LLM score cache keyed by model + prompt-relevant inputs
  - presentation cache or deterministic post-processing for `top_n`
  - response shaping for `dev_mode`
- Store superset results when possible, then slice/strip locally.
- Consider output-budget fields as execution parameters rather than semantic
  request inputs after a successful complete response.
- Keep model, prompt version, schema version, job target, candidate/evidence
  digest, and enrichment digest in the semantic key.

### 6. Bullet generation is completion-heavy and unconstrained

**Severity:** High

Current bullet generation produces long bullets. Completion tokens alone were:

- Project bullets: 5,565 completion tokens for 15 bullets
- Experience bullets: 5,854 completion tokens for 18 bullets

The prompt asks the model to maximize interview chances and produce polished
ATS-friendly bullets, but there is no hard word or character limit in the JSON
schema. The result is expensive and may produce bullets that are too long for
LaTeX layout or a one-page resume.

**Recommended design changes:**

- Add `maxLength` to bullet strings in the JSON schema.
- Add explicit target length, e.g. 18-28 words per bullet.
- Add a deterministic post-generation trim/check step.
- Let bullet count vary by record importance and evidence density.
- Use fewer bullets for weak-fit or sparse-evidence records.
- Consider model prompts that generate concise bullets first, then optionally
  polish selected bullets.

### 7. The full job target is repeated in every bullet request

**Severity:** Medium

Each project and experience bullet request repeats the job title and full job
description. With 11 bullet requests in the current run, the same job context is
paid for repeatedly.

**Recommended design changes:**

- Build a deterministic or cached `job_focus` object once per target:
  required skills, preferred skills, responsibilities, domain emphasis, and
  exclusions.
- Pass the compact `job_focus` to bullet generation instead of the full posting.
- Key it by job target digest and prompt/schema version.
- If the job description changes, regenerate only the focus summary and
  downstream stages that semantically depend on it.

### 8. Token usage accounting depends on dev details and misses failed attempts

**Severity:** Medium

Token usage is extracted from response `details`. If `dev_mode` is disabled,
details may be omitted and token usage becomes invisible to the generation
manifest. The current skill-selection failure also records 0 tokens because the
failure metadata was not captured as a usable response detail.

**Recommended design changes:**

- Separate internal telemetry from user-facing dev details.
- Always return or record stage usage metadata internally, even when `dev_mode`
  is false.
- Track failed attempts in the manifest, including parse failures and fallbacks.
- Add `degraded: true` or `fallback_reason` to `stage_responses`.

### 9. Cache entries do not store the canonical payload

**Severity:** Medium

Cache files store `version`, `stage`, `cache_key`, and `data`, but not the
canonical payload or payload digest details. This makes it hard to audit why a
cache entry exists, which config fields caused invalidation, or whether the
entry reflects a degraded fallback.

**Recommended design changes:**

- Store a redacted canonical payload in cache metadata.
- Store semantic digests separately: job target digest, evidence digest, config
  digest, prompt version, schema version.
- Store `source_quality`, `created_at`, `model`, `prompt_version`, and
  `degraded/fallback` flags.

### 10. Bullet generation is per-record only

**Severity:** Medium

Per-record caching is good for resume-after-failure behavior, but it repeats
shared instructions and job context for every selected item. With 11 records,
prompt overhead alone was 7,812 tokens for bullet stages.

**Recommended design changes:**

- Keep per-record cacheability, but allow batched generation by section when
  appropriate.
- Batch only records with small enough combined evidence to fit safely.
- Use a structured response keyed by record ID.
- On batch failure, fall back to per-record generation.
- Alternatively, cache a per-record "bullet library" keyed by evidence digest
  and do a cheap deterministic selection/trim step for each resume run.

### 11. Link scanning is project-only despite experience links

**Severity:** Medium

`ExperienceRecord` supports `links`, and current evidence includes links for
several experience entries. The generation pipeline only calls
`enrich_projects_with_link_scanning`; there is no corresponding experience link
scanner.

**Recommended design changes:**

- Add experience link enrichment as part of the separate evidence-enrichment
  workflow.
- Store scanned facts in experience evidence before bullet generation.
- Avoid doing this inside the normal generation run unless explicitly requested.

### 12. The pipeline calls the local FastAPI app over HTTP

**Severity:** Medium

The local orchestration layer calls local service endpoints through HTTP. This
keeps API contracts consistent, but it also introduces request timeout failures,
JSON serialization overhead, and a need to keep a local server running. The
prior agentic run hit a 30-second timeout during bullet generation.

**Recommended design changes:**

- Keep public HTTP endpoints, but add direct in-process adapters for the local
  generation pipeline.
- Put cache and telemetry at a shared service boundary so HTTP and direct paths
  behave the same.
- Keep HTTP mode as an integration test/deployment mode.

### 13. Resume result lacks provenance and claim auditability

**Severity:** Medium

The final `resume_result.json` contains only assembled content. It does not link
each generated bullet to source highlights, scanned links, cache entries, or
fallback state. The manifest now captures some stage metadata, but provenance is
not attached at bullet level.

**Recommended design changes:**

- Extend bullet results with source references:
  - evidence record ID
  - source highlight IDs or source URLs
  - generated-from cache key
  - model/prompt version
- Add a validation stage that flags bullets with unsupported terms or claims.
- Keep final LaTeX clean, but keep `resume_result.json` or a companion artifact
  self-auditing.

### 14. Bullet range is semantic and should remain cache-key relevant

**Severity:** Medium

`bullet_count_range` is used in the bullet prompt, instructions, JSON schema
`minItems`/`maxItems`, and local validation. It is not merely a presentation
parameter like `top_n`.

**Recommended design changes:**

- Keep `bullet_count_range` in semantic cache keys.
- Use range intentionally to reduce cost:
  - strong selected projects: 2-3 bullets
  - weak or sparse entries: 1 bullet
  - non-selected projects: 0 bullets
- Consider deriving default ranges from project score and evidence richness.

### 15. Project selection should scale with candidate count

**Severity:** Low to Medium

The current project set is small, so project selection cost is acceptable. As
project evidence grows, sending every candidate to the LLM will become wasteful.

**Recommended design changes:**

- Use deterministic baseline scoring as a cheap first-pass shortlist.
- Send only the top N or uncertain candidates to LLM reranking.
- Keep a manual override to force inclusion/exclusion.

### 16. Stage controls are too coarse for iterative work

**Severity:** Low to Medium

The current pipeline always proceeds through selection, optional link scanning,
project bullets, experience bullets, assembly, and artifact writing. Cache makes
reruns cheaper, but there is no first-class way to say "only refresh experience
bullets" or "only assemble from cached results."

**Recommended design changes:**

- Add run modes:
  - `select-only`
  - `enrich-only`
  - `bullets-only`
  - `assemble-only`
  - `full`
- Add per-stage force refresh controls instead of only global
  `cache.force_refresh`.
- Let users freeze selected projects/skills for a target and regenerate only
  bullets or LaTeX.

## Suggested Implementation Order

1. Fix skill-selection robustness:
   - computed output budget
   - retry on parse failure
   - do not silently cache degraded fallback as normal success
   - recursive role-profile inheritance and job-description-aware baseline

2. Add selection gating before expensive stages:
   - default `project_selection.top_n`
   - score threshold
   - skip bullet generation for weak projects

3. Redesign cache semantics:
   - separate raw LLM caches from response-shaping caches
   - ignore `top_n` and `dev_mode` at the raw-cache level
   - store payload metadata and quality flags

4. Split link scanning into durable evidence enrichment:
   - project and experience support
   - persisted scanned highlights with provenance
   - manual/stale/force scan policies

5. Reduce bullet cost:
   - concise schema and prompt constraints
   - variable bullet ranges by score/evidence
   - compact cached job focus
   - optional section batching with per-record fallback

6. Improve observability:
   - always record token usage independent of `dev_mode`
   - include failed attempts and degraded status in the manifest
   - add bullet-level provenance in the structured result

## Design Direction

The strongest efficiency improvement is to separate durable evidence enrichment
from resume drafting. Link scanning, repository exploration, and source
extraction should update evidence records when the user asks or when source
digests are stale. Normal resume generation should operate on already-curated
evidence, choose a small targeted subset, and generate concise bullets only for
records that will actually appear in the final artifact.

