### 2026-07-23 - Document Local-First Desktop App Plan

**Agent:** Codex (GPT-5)

**Changes:**
- `docs/decisions/016-local-first-web-workbench-desktop-distribution.md` - Added an accepted ADR for building the first product surface as a local-first web workbench over FastAPI, with desktop packaging as the first distribution target.
- `docs/decisions/README.md` - Added ADR 016 to the current ADR index.
- `README.md` - Added product direction for the local-first workbench, monorepo frontend, local backend, desktop packaging path, and deferred hosted multi-user concerns.
- `docs/devlog/Index.md` - Added this session entry.

**Rationale:**
The recommendation aligns with the current FastAPI facade, YAML-backed evidence storage, local artifact generation, and the repository guardrail against premature auth/database infrastructure. Documenting the decision as an ADR keeps the product packaging direction explicit before frontend implementation begins.

**Tests:**
- Not run; documentation-only change.

**Impact:**
This gives future frontend and packaging work a clear direction: build the usable local web workflow first, keep backend writes and generation centralized in FastAPI, and package the proven app as desktop before pursuing a hosted service.
