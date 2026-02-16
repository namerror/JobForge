You are an engineering assistant working on the Skill Relevance Selector microservice.
Your goal is to help implement features safely and incrementally.

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
- work is logged in `docs/dev-log.md`

## Development Logging (required)

After completing any non-trivial task or making architectural decisions, you MUST document your work in the appropriate log file.

### Session Log (`docs/dev-log.md`)
After completing tasks, append an entry with:
- **Date & Summary**: ISO date + brief task description (1 line)
- **Changes**: Files modified/created with line references where relevant
- **Rationale**: Why you made certain decisions or chose this approach
- **Tests**: What tests were added/modified and what they validate
- **Impact**: What this enables, fixes, or unlocks for future work

**Format:**
```markdown
### YYYY-MM-DD - [Brief Summary]

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
For user-facing changes, update using [Keep a Changelog](https://keepachangelog.com/) format:
- **Added**: new features
- **Changed**: changes to existing functionality
- **Fixed**: bug fixes
- **Removed**: removed features

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