### 2026-03-07 - Optimize agent logging instructions

**Agent:** GitHub Copilot (Claude Sonnet 4.5)

**Changes:**
- `AGENTS.md` - Rewrote "Development Logging" section with clarified CHANGELOG scope, detailed dev log requirements, new file naming convention (`MM-DD-YYYY-AgentName-description.md`), and required `Agent & Model` field in session files
- `CLAUDE.md` - Applied identical updates to the "Development Logging" section (kept in sync with AGENTS.md)
- `docs/devlog/README.md` - Rewrote to include naming convention, required content fields, a clear table showing what belongs in CHANGELOG vs. dev logs, and a full session index

**Rationale:**
The previous logging instructions were vague about when to use CHANGELOG vs. dev logs, had no file naming standard, and did not require agents to identify themselves or the model version they ran on. This made it difficult to trace which agent made which changes and caused CHANGELOG to accumulate noise (bug fixes, test additions) that obscures genuine user-facing releases. The new instructions enforce a clear split: CHANGELOG for big user-facing features only, dev logs for everything else (detailed, per-session).

**Tests:**
- No code changes; no tests required.

**Impact:**
- Future agent sessions will produce consistently named, detailed dev log files attributed to a specific agent and model version.
- CHANGELOG will remain clean and release-focused.
- Easier to audit session history and trace decisions back to the agent/model that made them.
