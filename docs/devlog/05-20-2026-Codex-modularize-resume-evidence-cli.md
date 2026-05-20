### 2026-05-20 - Modularize resume evidence CLI

**Agent:** Codex (GPT-5)

**Changes:**
- `app/resume_evidence/cli.py` - Reduced the module to the CLI entrypoint and schema dispatch path.
- `app/resume_evidence/base_cli.py` - Added the shared interactive CLI base with common prompt, confirmation, and output helpers.
- `app/resume_evidence/projects_cli.py` - Moved project-evidence command handling into its own module.
- `app/resume_evidence/skills_cli.py` - Moved skills-evidence command handling into its own module.
- `docs/agent-context-index.md`, `README.md`, `docs/architecture-overview.md`, `docs/branch-03-grounded-resume-generation.md` - Updated repo navigation and architecture docs so they describe `cli.py` as the entrypoint/dispatcher and point readers to the split command modules.

**Rationale:**
The CLI had grown into a mixed entrypoint-and-implementation module. Splitting the shared prompt helpers and the schema-specific command handlers makes the structure easier to navigate without changing the public CLI command surface. The follow-up doc updates keep the code map aligned with the new layout so future agents do not assume `cli.py` still contains all command logic.

**Tests:**
- No behavioral test changes were needed because `tests/test_resume_evidence_cli.py` already exercises `app.resume_evidence.cli.main`, which remains the public entrypoint.
- Sanity check target: existing CLI tests should continue to validate both project and skills flows through the dispatcher.

**Impact:**
This keeps the resume-evidence CLI easier to maintain as more evidence workflows are added, while preserving the same invocation path and user-facing command behavior.
