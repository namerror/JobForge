### 2026-06-09 - Add GitHub repository link scanning mode

**Agent:** Codex (GPT-5)

**Changes:**
- `app/link_scanning/llm_client.py:30-89` - Added URL-based scan target classification for normal single-page links and public `github.com/{owner}/{repo}` repository links.
- `app/link_scanning/llm_client.py:116-184` - Updated prompt payload and instructions with per-target scan modes, allowing GitHub repository-scoped exploration while preserving single-page behavior for normal links.
- `app/link_scanning/llm_client.py:258-344` - Added source URL validation that permits GitHub highlights from pages under the same repository scope and rejects cross-repo sources.
- `app/link_scanning/llm_client.py:347-445` - Added scan target metadata to link-scanning LLM result details.
- `tests/test_link_scanning_llm_client.py:57-380` - Added coverage for GitHub URL classification, mixed prompt payloads, same-repo source acceptance, and cross-repo source rejection.
- `README.md:331-332` and `docs/CHANGELOG.md` - Documented GitHub repository-scoped link scanning behavior.

**Rationale:**
GitHub repository links contain richer project evidence than ordinary web pages. The scanner now distinguishes GitHub repository targets so the LLM can inspect README, source files, docs, tests, and config pages within the same repo without weakening provenance checks or allowing unrestricted browsing.

**Tests:**
- `test_classify_link_scan_target_detects_github_repo_roots_and_subpaths`: validates root and subpath GitHub repo URLs are classified as repository scans.
- `test_build_link_scan_prompt_payload_marks_github_repo_targets`: validates prompt payload includes GitHub repo mode and repo-scoped instructions.
- `test_scan_project_links_with_llm_accepts_same_github_repo_source`: validates same-repo GitHub source URLs are accepted.
- `test_scan_project_links_with_llm_rejects_other_github_repo_source`: validates cross-repo GitHub source URLs are rejected.
- `PYTHONPATH=. .venv/bin/python -m pytest tests/test_link_scanning_llm_client.py tests/test_link_scanning_api.py tests/test_resume_generation.py`: 32 passed.

**Impact:**
Link scanning can now collect stronger technical project evidence from GitHub repositories while preserving deterministic source validation, highlight-only enrichment, and strict failure behavior.
