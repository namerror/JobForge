### 2026-02-25 - Split dev log into session files

**Changes:**
- `docs/devlog/README.md` - Added index of per-session log files
- `docs/devlog/2026-02-25-2026-02-25-add-agent-architecture-overview-and-instruction-index.md` - Moved existing session entry into its own file
- `docs/devlog/2026-02-24-2026-02-24-migrate-role-profiles-from-python-dict-to-yaml-files.md` - Moved existing session entry into its own file
- `docs/devlog/2026-02-17-2026-02-17-implement-eval-case-scoring-function.md` - Moved existing session entry into its own file
- `docs/devlog/2026-02-17-2026-02-17-expand-eval-cases-to-20-realistic-user-inputs.md` - Moved existing session entry into its own file
- `docs/devlog/2026-02-16-2026-02-16-add-comprehensive-tests-for-baseline-select-skills-function.md` - Moved existing session entry into its own file
- `docs/devlog/2026-02-16-2026-02-16-complete-test-suite-for-baseline-scoring.md` - Moved existing session entry into its own file
- `docs/dev-log.md` - Replaced inline entries with pointer to `docs/devlog/`
- `AGENTS.md` - Updated logging instructions to require per-session files under `docs/devlog/`
- `CLAUDE.md` - Updated logging instructions to require per-session files under `docs/devlog/`

**Rationale:**
Splitting logs by session keeps entries immutable, easier to scan, and avoids merge conflicts in a single large file.

**Tests:**
- No automated tests added or run (documentation-only changes).

**Impact:**
Logging is now per-session file under `docs/devlog/`, with a stable index for navigation.
