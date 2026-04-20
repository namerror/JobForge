# Branch 03: Grounded Resume Generation

## Purpose
This branch is the first expansion beyond skill selection. Its planning focus is a user-friendly, file-based evidence pipeline for grounded resume generation, not a schema reference or polished free-form resume generator.

Treat this document as a guide for future implementation work. Exact YAML schemas, field-level validation rules, and concrete resume output contracts should be designed incrementally during implementation.

## Current Repo Context
- The current production request/response contract is `SkillSelectRequest` and `SkillSelectResponse` in `app/models.py`.
- Implemented methods today are `baseline`, `embeddings`, and `llm`; service dispatch lives in `app/services/skill_selector.py`. An optional baseline filter can pre-handle recognized skills before model-backed methods score the unrecognized remainder.
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
- Define a future-facing resume pipeline around user-authored YAML evidence files, deterministic validation, grounded synthesis, and deterministic assembly.
- Use planned `data/resume_evidence/` YAML files as the canonical source of truth for resume facts:
  - `data/resume_evidence/skills.yaml`
  - `data/resume_evidence/profile.yaml`
  - `data/resume_evidence/experience.yaml`
  - `data/resume_evidence/projects.yaml`
- Build a runtime evidence index from those files at run time. The index is derived, rebuildable, and created without LLM or NLP behavior.
- Use planned `app/data/resume_formats/` files for reusable resume outline/style definitions.
- Keep data synthesis/extraction as the core feature: it reads the job target, evidence index, selected skills, and resume format needs, then returns structured fill data with evidence traceability.
- Keep deterministic assembly separate from synthesis. Assembly follows the selected outline and must not select, infer, invent, or rewrite claims.
- Preserve hard grounding rules:
  - generated claims must be supported by user evidence
  - job descriptions may guide prioritization, but they are never evidence of user experience
  - unsupported claims must be omitted, not guessed
- Treat skill selection as one prioritization signal for resume drafting, not the entire source of truth.

## Quick Guide
1. Start with the file-based evidence source-of-truth model before implementing resume generation.
2. Implement YAML schemas incrementally, one evidence file at a time; `projects.yaml` is the likely first candidate.
3. Validate evidence files deterministically and build a runtime evidence index with stable traceability.
4. Define resume format/outline resources separately from user evidence.
5. Implement synthesis/extraction as the layer that selects and prepares supported data for a target job and format.
6. Keep rephrasing as a future extension point inside synthesis, not deterministic assembly.
7. Build evaluation around factual support, relevance, compression quality, section budget compliance, and token efficiency.
8. Defer polished prose generation until the evidence, synthesis, and grounding layers are inspectable and benchmarked.

## Interfaces And Resources
- This branch introduces a future-facing pipeline. It does not change the current production `/select-skills` contract until separate implementation work is approved.
- Planned source-of-truth evidence files live under `data/resume_evidence/`. These paths are future conventions, not existing implemented schemas:
  - `skills.yaml` stores skill evidence authored by the user.
  - `profile.yaml` stores profile-level evidence authored by the user.
  - `experience.yaml` stores work-history evidence authored by the user.
  - `projects.yaml` stores project evidence authored by the user and is the likely first file to specify during implementation.
- Planned resume format definitions live under `app/data/resume_formats/`. These files should describe reusable outline/style policy, such as section order, section budgets, required slots, optional slots, and deterministic assembly rules.
- Runtime evidence index responsibilities:
  - load user-authored YAML evidence files
  - validate structure and identifiers deterministically
  - expose lookup and traceability for synthesis
  - remain rebuildable from source files
  - avoid LLM/NLP behavior
- Synthesis/extraction responsibilities:
  - consume the job target, evidence index, selected skills, and resume format needs
  - select supporting evidence
  - prepare structured fill data for assembly
  - preserve evidence traceability for each generated claim or highlight
  - initially return evidence text as-is when rephrasing is not implemented
- Assembly responsibilities:
  - consume a selected resume format and structured fill data
  - render according to deterministic outline rules
  - avoid selecting, inferring, rephrasing, or inventing claims
- Shared existing resources still matter here:
  - `app/models.py`
  - `app/services/skill_selector.py`
  - `app/scoring/*`
  - `data/eval_cases/*.json`
- Treat `data/eval_runs/` as a future convention for saved benchmark outputs, and treat any resume-specific fixtures as future additions rather than existing repository assets.
- Generated resumes and benchmark runs are artifacts, not source-of-truth profile memory. Generation must not silently mutate user-authored evidence YAML files.

## Agent Implementation Guidance
- Treat this document as a design guide, not a schema reference.
- Do not add detailed YAML field schemas to this planning doc.
- Implement schemas incrementally, starting with one YAML file at a time.
- Each schema implementation should include validation, tests, and a devlog entry.
- The first implementation pass should likely start with `projects.yaml`, but exact fields and validation rules should be decided during that pass.
- Keep resume-generation work grounded and inspectable before adding model-backed rephrasing.
- Do not add database dependencies for the initial file-based design.
- Do not make YAML files mutate silently during generation.
- Keep rephrasing behind a synthesis/extraction interface so deterministic assembly remains stable even if future rephrasing becomes model-backed.

## Benchmarking And Verification
- Build a benchmark plan that scores:
  - factual support and evidence coverage
  - relevance to the target job
  - compression quality
  - resume section budget compliance
  - omission of unsupported claims
  - token and latency efficiency
- Add checks that every generated statement can be traced back to one or more evidence IDs.
- Keep the first milestone structured and inspectable so failures are easy to diagnose before prose generation is attempted.
- Do not score this branch only on fluency; factual grounding and supportability are the primary quality gates.
