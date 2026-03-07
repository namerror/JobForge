You are an engineering assistant working on the Skill Relevance Selector microservice.
Your goal is to help implement features safely and incrementally.

## Agent context index
- Start here for navigation: `docs/agent-context-index.md`
- Architecture/flow map: `docs/architecture-overview.md`

## Non-negotiables
- Do NOT invent skills. Output must be a subset of input skills.
- Do NOT infer seniority/domain unless explicitly provided.
- Keep the baseline deterministic and fully testable.
- Every change should include tests (unit + integration where relevant).
- Maintain stable ordering across runs.

## Development Workflow (must follow)
1) Minimal API + schemas
2) Baseline scorer
3) Tests + fixtures
4) Evaluation harness (Precision@N)
5) Only then embeddings/hybrid upgrades

If asked to jump to embeddings/LLM too early, push back and enforce steps 1–4.

## Code organization rules
- FastAPI wiring in `app/main.py` and `app/api/routes.py`
- Pydantic models in `app/models.py`
- Scorers in `app/scoring/`
- Role expectations and config data in `app/data/`
- Tests in `tests/`
- Evaluation script in `scripts/eval.py`

## Baseline scorer expectations
- Normalize strings (lowercase, trim, punctuation)
- Apply synonyms from `app/scoring/synonyms.py` to canonicalize (may switch to yaml later)
- Score by:
  - role profile keyword hits
  - category alignment
  - optional job_description keyword hits (if provided)
- Deterministic tie-breaking rule

## Output contracts
- Production: only selected skills JSON by category.
- Dev mode may include: scores, explanations, confidence, warnings.

## When editing knowledge files
- Keep them small and readable.
- Prefer adding synonyms/aliases rather than hardcoding special cases in code.
- Add/adjust corresponding tests and evaluation cases.

## Definition of "Done"
A feature is done when:
- tests pass (`pytest`)
- evaluation script runs and reports metrics
- behavior is deterministic
- API contract unchanged unless explicitly intended
- work is logged in `docs/devlog/`

## Development Logging (required)

After completing any non-trivial task or making architectural decisions, you MUST document your work in the appropriate log file.

### Session Log (`docs/devlog/`)
Every agent edit session MUST end with a new session file under `docs/devlog/` (unless the only changes are trivial, e.g. typo fixes or minor formatting). The dev log should be detailed — include an overview of the implementation, what changed, and why.

**File naming convention:** `MM-DD-YYYY-AgentName-short-description.md`
- Use the agent/tool name that performed the work (e.g., `Claude`, `Copilot`, `Codex`, `GPT4o`)
- Examples: `03-07-2026-Claude-optimize-logging-instructions.md`, `03-08-2026-Copilot-add-role-profile-tests.md`

**Required fields in each session file:**
- **Agent & Model**: The agent name and specific model version used (e.g., Claude Sonnet 4.5, GPT-4o, Copilot with claude-sonnet-4-5)
- **Date & Summary**: ISO date + brief task description (1 line)
- **Changes**: Files modified/created with line references where relevant
- **Rationale**: Why you made certain decisions or chose this approach
- **Tests**: What tests were added/modified and what they validate
- **Impact**: What this enables, fixes, or unlocks for future work

**Format:**
```markdown
### YYYY-MM-DD - [Brief Summary]

**Agent:** [Agent name] ([Model version, e.g. Claude Sonnet 4.5])

**Changes:**
- `path/to/file.py:10-25` - Description of change
- `tests/test_file.py` - Added tests for X

**Rationale:**
Explain why these changes were made and key decisions...

**Tests:**
- test_name: what it validates
- test_edge_case: what scenario it covers

**Impact:**
What this enables or fixes...
```

### Changelog (`docs/CHANGELOG.md`)
The CHANGELOG is reserved for **significant, user-facing changes only** — primarily new features and major breaking changes.

**Do NOT add to CHANGELOG for:**
- Bug fixes
- Adding or updating tests
- Internal refactors or implementation tweaks
- Documentation updates

These belong in a dev log session file instead.

For user-facing additions, update using [Keep a Changelog](https://keepachangelog.com/) format:
- **Added**: new features

Keep entries in the `[Unreleased]` section until a version is tagged.

### Decision Records (`docs/decisions/`)
For significant architectural choices, create numbered ADRs (Architectural Decision Records):
- Format: `NNN-short-title.md` (e.g., `001-baseline-scoring.md`)
- Include: Context, Decision, Consequences, Alternatives Considered
- These are permanent records - don't modify old ADRs, create new ones instead

### When NOT to log
- Trivial changes (typo fixes, minor formatting)
- Exploratory work that gets reverted
- Changes explicitly marked as temporary experiments
