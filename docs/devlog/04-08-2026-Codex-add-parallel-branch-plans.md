### 2026-04-08 - Add parallel branch planning docs for hybrid, LLM, and grounded resume work

**Agent:** Codex (GPT-5)

**Changes:**
- `docs/branch-01-hybrid-skill-selection.md` - Added a branch planning spec for hybrid scoring with a fixed fusion recipe, fallback rules, shared resources, and benchmark expectations.
- `docs/branch-02-llm-skill-selection.md` - Added a branch planning spec for pure LLM-based skill selection with structured JSON output, strict validation, deterministic local ranking, and cost-aware evaluation.
- `docs/branch-03-grounded-resume-generation.md` - Added a branch planning spec for future grounded resume generation centered on evidence extraction, structured synthesis, and traceable claims.
- `docs/devlog/04-08-2026-Codex-add-parallel-branch-plans.md` - Logged the repo review outcome and the shared conventions used across the three branch docs.

**Rationale:**
The project is expanding from deterministic skill selection into multiple parallel lines of work, and the immediate need was to create branch-ready specs that do not drift on core contracts. I kept the top-level structure identical across the three docs and copied the same Shared Contract section verbatim so parallel work can reuse the same categories, source-of-truth files, API conventions, and benchmark dimensions. The resume-generation branch was intentionally scoped to extraction plus grounded structured output rather than polished prose so future work stays aligned with the repo's emphasis on rigor and non-invented claims.

**Tests:**
- No automated tests were added because this task created planning documentation only.
- Performed static repo review to align the docs with existing files and contracts, including `app/models.py`, `app/services/skill_selector.py`, `app/scoring/`, `data/eval_cases/`, and current docs.
- Attempted local `pytest` collection, but the environment is currently missing required packages such as `fastapi`, `dotenv`, and `openai`, so runtime verification is blocked until dependencies are installed.

**Impact:**
These docs give the three planned branches a common operating contract before implementation starts, which reduces schema drift and inconsistent evaluation practices. They also separate the concerns of hybrid ranking, pure LLM selection, and grounded resume generation so each branch can progress in parallel without redefining shared resources or baseline guarantees.
