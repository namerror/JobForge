### 2026-03-10 - Add CLI flags to eval.py for flexible eval case selection

**Agent:** Claude (Opus 4.6)

**Changes:**
- `scripts/eval.py` - Replaced hardcoded file loading with argparse CLI, added `load_cases()` to handle both eval case formats

**Rationale:**
The eval script had hardcoded paths to `eval_cases_basic.json` and `eval_cases_real.json`, loaded at module level. With the new eval cases generator producing files in `data/eval_cases/generated/`, the script needed flexible file selection.

Key changes:
- Removed module-level file loading (`eval_real`, `eval_basic` globals)
- Added `load_cases()` that handles both formats: bare JSON arrays (existing files) and wrapped `{"metadata": ..., "cases": [...]}` (generated files)
- Added `-f` / `--file` flag: accepts a filename (resolved relative to `data/eval_cases/`), relative path, or absolute path
- Added `--run-generated` flag: runs eval against all files in `data/eval_cases/generated/`, printing results per file
- `-f` and `--run-generated` are mutually exclusive; default (no flags) runs `eval_cases_basic.json`
- `evaluate()` now takes a `cases` list directly instead of loading files internally
- Added `resolve_file()` for flexible path resolution

**Tests:**
- Manually verified all three modes: default, `-f eval_cases_real.json`, `--run-generated`
- Verified mutual exclusivity error when both flags are provided
- Verified generated files (wrapped format) are loaded correctly

**Impact:**
- Eval script now works seamlessly with both hand-crafted and generated eval case files
- `--run-generated` enables batch evaluation across all generated datasets
