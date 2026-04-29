### 2026-04-29 - Add Request Payloads To Agentic Report

**Agent:** Codex (GPT-5)

**Changes:**
- `docs/notes/04-29-2026-Codex-agentic-skill-selection-no-embeddings-test.md` - Added compact request payloads before each evaluated response.
- `docs/agentic-testing/agent-testing-guide.md` - Updated report guidance and template to require readable request/response pairs.
- `docs/devlog/Index.md` - Added this session entry.

**Rationale:**
The report is easier to audit when each response is paired with the exact request options and candidate inputs that produced it. The guide now makes this expectation explicit for future agentic testing reports.

**Tests:**
- Documentation-only update; ran markdown/diff whitespace validation.

**Impact:**
Future testing notes should be self-contained enough to review without opening raw JSON result files.
