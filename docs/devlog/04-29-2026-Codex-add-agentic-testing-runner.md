### 2026-04-29 - Add Agentic Testing Runner

**Agent:** Codex (GPT-5)

**Changes:**
- `docs/agentic-testing/run_agentic_dataset.py` - Added a flexible dataset runner with suite, input-set, variant, exclude-variant, dry-run, output, timeout, and fail-on-error options.
- `docs/agentic-testing/dataset.json` - Added explicit suite endpoint fields for `/select-skills` and `/select-projects`.
- `docs/agentic-testing/README.md` - Documented the runner file.
- `docs/agentic-testing/agent-testing-guide.md` - Added workable `.venv` and runner-based execution steps.
- `docs/devlog/Index.md` - Added this session entry.

**Rationale:**
The runner avoids hard-coded manual REST calls and lets agents select exactly which dataset items to execute, including skill-only runs and model-backed variant exclusions. Explicit endpoint fields keep the dataset self-describing for future suites.

**Tests:**
- Ran the script help output to validate CLI parsing.
- Ran dry-run selections for skill-only requests excluding embeddings.
- Parsed `dataset.json` with `jq`.

**Impact:**
Agents can now execute repeatable API test subsets from the dataset and capture structured JSON results for notes-style review reports.
