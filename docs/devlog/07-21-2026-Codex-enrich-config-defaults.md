### 2026-07-21 - Enrich CLI Config Defaults

**Agent:** Codex (GPT-5)

**Changes:**
- `resume_generation/enrich.py:273-341` - Added a config-path pre-parser, loaded the generation config before full CLI parsing, defaulted link scanning CLI arguments from `link_scanning`, and added `--dev-mode` / `--no-dev-mode`.
- `tests/test_resume_generation.py:1586-1672` - Added CLI regression coverage for config-backed defaults and explicit CLI overrides.

**Rationale:**
The enrichment runner already supported config-backed values when callers passed `None`, but the CLI did not expose `dev_mode` and did not present config values as argument defaults. Loading the config before full parsing makes `user/resume_generation/config.yaml` the source of truth while preserving CLI override behavior.

**Tests:**
- `test_enrich_main_uses_link_scanning_config_defaults`: validates omitted CLI arguments are populated from `link_scanning`, including a null token budget.
- `test_enrich_main_cli_args_override_link_scanning_config`: validates explicit CLI arguments override configured defaults, including `--no-dev-mode`.
- `PYTHONPATH=. .venv/bin/pytest tests/test_resume_generation.py -q`: 68 passed.

**Impact:**
Running `resume_generation/enrich.py` now consistently uses the user-level resume generation config for link scanning defaults, while keeping per-run overrides available from the command line.
