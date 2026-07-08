### 2026-07-08 - LaTeX Resume Output

**Agent:** Codex (GPT-5)

**Changes:**
- `resume_generation/latex.py:16-345` - Added template-based LaTeX rendering, reserved-character escaping, output path resolution, and atomic `.tex` artifact writing for `IntermediateResumeResult`.
- `resume_generation/models.py:189-214` - Added the typed `resume_output` config section with blank/null path support.
- `resume_generation/main.py:25-294` - Added the config-driven LaTeX writer helper and wired it into the direct script entrypoint after `run_resume_generation_pipeline()`.
- `resume_generation/__init__.py:14-98` - Exported the new output config and LaTeX helper APIs.
- `tests/test_resume_generation.py:371-444` and `tests/test_resume_generation.py:1216-1300` - Added config, escaping, renderer, artifact writing, and entrypoint-helper coverage.
- `docs/CHANGELOG.md:10-12` - Documented the user-facing LaTeX resume output feature under Unreleased.

**Rationale:**
The pipeline already assembles a structured runtime resume result and writes the JSON artifact. Rendering LaTeX from that in-memory result keeps final output generation deterministic and avoids re-reading intermediate JSON. Limiting the `.tex` write to the `__main__` entrypoint preserves library-call behavior while enabling the script path to produce the final resume artifact.

**Tests:**
- `test_load_generation_config_accepts_resume_output_path`: validates explicit output path config.
- `test_load_generation_config_defaults_blank_resume_output_path`: validates blank path fallback to the default `.tex` artifact path.
- `test_latex_escape_escapes_reserved_characters`: validates escaping for LaTeX-reserved characters.
- `test_render_resume_latex_uses_template_sections_and_runtime_result`: validates template section order and runtime result insertion.
- `test_write_resume_latex_artifact_writes_tex_file`: validates atomic `.tex` artifact creation.
- `test_write_resume_latex_from_config_writes_configured_output`: validates the script-entry helper and structured log event.
- `PYTHONPATH=. pytest tests/test_resume_generation.py`: validates the resume-generation test suite.

**Impact:**
Running `resume_generation/main.py` can now produce a final LaTeX resume file from the generated resume result, with configurable output path support and the template structure preserved for the current data model.
