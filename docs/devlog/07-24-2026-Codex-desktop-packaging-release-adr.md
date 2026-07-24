### 2026-07-24 - Document Desktop Packaging and Release Workflow

**Agent:** Codex (GPT-5)

**Changes:**
- `docs/decisions/017-desktop-packaging-and-release-workflow.md` - Added an accepted ADR documenting the preferred Tauri plus Python sidecar desktop packaging strategy, phased packaging plan, CI validation path, release workflow, and deferred update strategy.
- `docs/decisions/README.md` - Added ADR 017 to the current ADR index.
- `docs/devlog/Index.md` - Added this session entry.

**Rationale:**
The project already committed to a local-first React/Vite workbench over FastAPI in ADR 016. This ADR turns that direction into an operational packaging and release plan that future work can reference consistently, while preserving file-backed local storage and avoiding premature database, hosted service, or native UI rewrites.

**Tests:**
- Not run; documentation-only change.

**Impact:**
Future desktop work now has named phases for package hygiene, runtime data layout, desktop shell integration, CI validation, tagged releases, and update strategy.
