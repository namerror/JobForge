### 2026-04-27 - Smooth version consistency test

**Agent:** Codex (GPT-5)

**Changes:**
- `tests/test_version.py` - Replaced hard-coded current release assertions with SemVer validation and parsed changelog release headings.
- `docs/devlog/Index.md` - Added this session entry.

**Rationale:**
The previous test protected version/changelog drift but required editing test literals on every release. Parsing released changelog headings keeps the same guard while making future version bumps smoother.

**Tests:**
- `test_version_constant_uses_semver`: validates the central app version uses basic SemVer format.
- `test_changelog_contains_current_release_section`: validates the latest released changelog heading matches `app.__version__`.

**Impact:**
Future release bumps only need updates to the version source and changelog heading; the test code should not need per-release edits.
