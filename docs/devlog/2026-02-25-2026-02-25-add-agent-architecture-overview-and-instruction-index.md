### 2026-02-25 - Add agent architecture overview and instruction index

**Changes:**
- `docs/architecture-overview.md` - Added module dependency map, request flow diagram, scoring flow, and extension points for `app/`
- `docs/agent-context-index.md` - Added centralized index for agent instructions and recommended read order
- `AGENTS.md` - Added pointers to the new agent context index and architecture overview
- `CLAUDE.md` - Added pointers to the new agent context index and architecture overview

**Rationale:**
Agents needed a fast, explicit way to understand module relationships and runtime logic flow without repeating or fragmenting instruction context. A dedicated architecture document keeps flow knowledge separate from policy docs, while a single index file improves discoverability and onboarding speed.

**Tests:**
- No automated tests added or run (documentation-only changes).

**Impact:**
Reduces time-to-context for future agent sessions, makes dependency and control flow easier to trace, and keeps instruction files linked through one canonical navigation entry point.
