### 2026-03-10 - Build eval cases generator from skill pools

**Agent:** Claude (Opus 4.6)

**Changes:**
- `scripts/eval_cases_generator.py` - New script: generates eval cases by sampling from skill pool buckets (core/nice/exclude)
- `data/eval_cases/generated/` - New directory for generated output files
- `data/skill_pools/README.md` - Filled in "How to generate eval cases" placeholder with usage docs

**Rationale:**
The project needed an automated way to produce eval cases from skill pools rather than hand-crafting them. The generator samples relevant skills (core+nice) and noise (exclude) with configurable counts, creating realistic test inputs. Each generated file gets a unique timestamp+UUID to avoid overwrites across runs.

Key design decisions:
- Uses `random.Random` instance (not module-level) so `--seed` gives full reproducibility
- Role name variants (casing, whitespace, hyphens) are included to test normalization
- Ranking flag controls whether expected output orders core before nice (default: true), with alphabetical sort within each tier
- Output wraps cases in a metadata envelope recording all generation parameters
- N and M (relevant/noise counts) vary per case via random sampling within configured min/max ranges

**Tests:**
- No automated tests added yet — generator is a standalone CLI script. Verified manually:
  - Seed reproducibility (same seed → same output)
  - `--no-ranking` produces pure alphabetical expected output
  - `--ranking` places core skills before nice skills
  - All CLI flags work correctly

**Impact:**
- Enables scalable eval case generation as new roles are added to skill_pools.json
- Supports evaluation of both baseline and embedding scoring methods
- Fills the placeholder in the skill pools README
