### 2026-04-27 - Add CI workflow and version guard

**Agent:** Codex (GPT-5)

**Changes:**
- `.github/workflows/ci.yml` - Added the first GitHub Actions CI workflow for push and pull request pytest runs on Python 3.12.
- `app/__init__.py:1` - Added the centralized `__version__` constant for release metadata.
- `app/main.py:3-25` - Updated `/health` to report the centralized package version.
- `docs/CHANGELOG.md:8-30` - Cut the current user-facing changes into the `0.2.0` release dated 2026-04-27.
- `tests/test_version.py` - Added version consistency checks across code, health output, and changelog.

**Rationale:**
This creates a lightweight CI foundation without adding new linting or deployment policy before the project needs it. Centralizing the runtime version and testing it against the changelog keeps the public health endpoint and release notes from drifting.

**Tests:**
- `test_version_constant_matches_current_release`: validates the current release constant is `0.2.0`.
- `test_health_reports_package_version`: validates `/health` reports the same centralized version.
- `test_changelog_contains_current_release_section`: validates the release is documented in the changelog.
- Full suite intended command: `.venv/bin/python -m pytest`.

**Impact:**
Every push and pull request can now run deterministic non-smoke tests in GitHub Actions. Future releases have a small automated guard for keeping runtime and changelog version metadata aligned.
