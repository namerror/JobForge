### 2026-06-21 - Add Resume Result JSON Artifact

**Agent:** Codex (GPT-5)

**Changes:**
- `resume_generation/main.py:25-43` - Added the default `user/resume_generation/resume_result.json` artifact path and atomic JSON writer for `IntermediateResumeResult`.
- `resume_generation/main.py:46-113` - Added an optional artifact path override to the pipeline and write the assembled resume result before future LaTeX generation.
- `tests/test_resume_generation.py:720-777` - Added direct coverage for human-readable JSON artifact serialization.
- `tests/test_resume_generation.py:1020-1163` - Extended the pipeline orchestration test to assert the resume result artifact is written after assembly.
- `.gitignore:11-12` - Ignored generated resume-generation artifacts that may contain personal resume data.

**Rationale:**
The pipeline already assembles a structured intermediate resume result but discarded it. Persisting that model as pretty JSON gives users an inspectable preview and preserves the completed assembly output if later resume-generation stages fail.

**Tests:**
- `test_write_resume_result_artifact_writes_human_readable_json`: validates parent directory creation, indented JSON, newline termination, top-level shape, and serialized content.
- `test_resume_generation_pipeline_loads_config_job_and_evidence_once`: validates the pipeline writes the artifact after assembly while preserving existing orchestration behavior.
- `PYTHONPATH=. .venv/bin/pytest tests/test_resume_generation.py`

**Impact:**
Resume generation now produces a stable debug artifact at `user/resume_generation/resume_result.json` by default, creating a useful checkpoint before final LaTeX output exists.
