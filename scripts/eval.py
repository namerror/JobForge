"""Evaluate scoring methods against eval case datasets.

Usage:
    python scripts/eval.py                          # Run against eval_cases_basic.json (default)
    python scripts/eval.py -f eval_cases_real.json   # Run against a specific file
    python scripts/eval.py -f /absolute/path.json    # Absolute path also works
    python scripts/eval.py --run-generated            # Run against all generated eval case files

The scoring method is controlled by the METHOD setting (env var or .env file):
    METHOD=baseline  python scripts/eval.py         # Use baseline scorer (default)
    METHOD=embeddings python scripts/eval.py        # Use embedding scorer
    METHOD=llm       python scripts/eval.py         # Use LLM scorer
"""

import argparse
import json
import glob
from pathlib import Path
from app.scoring.baseline import baseline_select_skills
from app.scoring.embeddings import embedding_select_skills
from app.scoring.llm import llm_select_skills
from app.config import settings

REPO_ROOT = Path(__file__).parent.parent
EVAL_CASES_DIR = REPO_ROOT / "data" / "eval_cases"
GENERATED_DIR = EVAL_CASES_DIR / "generated"

CATEGORIES = ["technology", "programming", "concepts"]
EFFICIENCY_KEYS = ["api_calls", "prompt_tokens", "completion_tokens", "total_tokens"]


def load_cases(path: Path) -> list[dict]:
    """Load eval cases from a JSON file.

    Handles both formats:
    - Bare array: [{input, expected}, ...]
    - Wrapped: {"metadata": {...}, "cases": [{input, expected}, ...]}
    """
    with open(path) as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "cases" in data:
        return data["cases"]

    raise ValueError(f"Unrecognized eval case format in {path}")


def eval_case(selected_skills: dict, expected: dict) -> dict:
    """
    Compare selected_skills against expected (trimmed to top_n per category).

    Score per category: Jaccard index = |hits| / (|hits| + |missing| + |unexpected|)
    This penalises both missing expected items and unexpected extras equally.

    Returns:
        scores:        per-category Jaccard score (0-1)
        average_score: mean of the three category scores
        mistakes:      per-category lists of missing and unexpected items
    """
    top_n = settings.TOP_N
    scores = {}
    mistakes = {}

    for cat in CATEGORIES:
        selected_set = set(selected_skills.get(cat, []))
        expected_set = set(expected.get(cat, [])[:top_n])

        hits = selected_set & expected_set
        missing = sorted(expected_set - selected_set)
        unexpected = sorted(selected_set - expected_set)

        denominator = len(hits) + len(missing) + len(unexpected)
        scores[cat] = round(len(hits) / denominator, 4) if denominator > 0 else 1.0

        mistakes[cat] = {"missing": missing, "unexpected": unexpected}

    average_score = round(sum(scores.values()) / len(CATEGORIES), 4)

    return {
        "scores": scores,
        "average_score": average_score,
        "mistakes": mistakes,
    }

def select_skills(
    job_role: str,
    technology: list[str],
    programming: list[str],
    concepts: list[str],
    job_text: str | None = None,
) -> tuple[dict, dict | None]:
    """Dispatch to the scoring method specified by settings.METHOD."""
    method = settings.METHOD
    if method == "baseline":
        return baseline_select_skills(
            job_role=job_role,
            technology=technology,
            programming=programming,
            concepts=concepts,
            job_text=job_text,
            dev_mode=True,
            include_zero=False,
        )
    elif method == "embeddings":
        return embedding_select_skills(
            job_role=job_role,
            technology=technology,
            programming=programming,
            concepts=concepts,
            job_text=job_text,
            dev_mode=True,
        )
    elif method == "llm":
        return llm_select_skills(
            job_role=job_role,
            technology=technology,
            programming=programming,
            concepts=concepts,
            job_text=job_text,
            dev_mode=True,
        )
    else:
        raise ValueError(
            f"Unknown scoring method: {method!r} (expected 'baseline', 'embeddings', or 'llm')"
        )


def extract_efficiency(details: dict | None) -> dict:
    """Extract comparable model-cost metadata from scorer details when present."""
    llm_meta = details.get("_llm", {}) if isinstance(details, dict) else {}
    return {
        "api_calls": int(llm_meta.get("api_calls", 0) or 0),
        "prompt_tokens": int(llm_meta.get("prompt_tokens", 0) or 0),
        "completion_tokens": int(llm_meta.get("completion_tokens", 0) or 0),
        "total_tokens": int(llm_meta.get("total_tokens", 0) or 0),
        "latency_ms": float(llm_meta.get("latency_ms", 0.0) or 0.0),
    }


def evaluate(cases: list[dict]) -> dict:
    results = []
    score_sum = 0.0
    efficiency_totals = {
        "api_calls": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "latency_ms": 0.0,
    }
    for case in cases:
        job_role = case["input"]["job_role"]
        technology = case["input"]["technology"]
        programming = case["input"]["programming"]
        concepts = case["input"]["concepts"]
        job_text = case["input"].get("job_text")

        expected = case["expected"]

        selected_skills, details = select_skills(
            job_role=job_role,
            technology=technology,
            programming=programming,
            concepts=concepts,
            job_text=job_text,
        )

        evaluation = eval_case(selected_skills, expected)
        efficiency = extract_efficiency(details)
        for key in EFFICIENCY_KEYS:
            efficiency_totals[key] += efficiency[key]
        efficiency_totals["latency_ms"] += efficiency["latency_ms"]

        results.append({
            "job_role": job_role,
            "evaluation": evaluation,
            "efficiency": efficiency,
        })

        score_sum += evaluation["average_score"]

    average_score = round(score_sum / len(results), 4)
    return {
        "method": settings.METHOD,
        "results": results,
        "overall_score": average_score,
        "efficiency_totals": {
            **{key: efficiency_totals[key] for key in EFFICIENCY_KEYS},
            "latency_ms": round(efficiency_totals["latency_ms"], 3),
        },
        "top_n": settings.TOP_N,
    }


def resolve_file(file_arg: str) -> Path:
    """Resolve a file argument to an absolute path.

    If it's already absolute or exists relative to cwd, use it directly.
    Otherwise, look in the eval_cases directory.
    """
    p = Path(file_arg)
    if p.is_absolute():
        return p
    if p.exists():
        return p.resolve()
    # Try relative to eval_cases dir
    candidate = EVAL_CASES_DIR / file_arg
    if candidate.exists():
        return candidate
    raise FileNotFoundError(f"Eval case file not found: {file_arg} (also checked {candidate})")


def collect_generated_files() -> list[Path]:
    """Collect all generated eval case files, sorted by name."""
    if not GENERATED_DIR.exists():
        return []
    files = sorted(GENERATED_DIR.glob("*.json"))
    return files


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate scoring methods against eval case datasets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-f", "--file", type=str, default=None,
        help="Eval case file to run. Can be a filename in data/eval_cases/, a relative path, or an absolute path.",
    )
    group.add_argument(
        "--run-generated", action="store_true",
        help="Run against all generated eval case files in data/eval_cases/generated/.",
    )

    args = parser.parse_args()

    if args.run_generated:
        files = collect_generated_files()
        if not files:
            print(f"No generated eval case files found in {GENERATED_DIR}")
            return

        print(f"Method: {settings.METHOD}")
        for filepath in files:
            cases = load_cases(filepath)
            print(f"\n{'='*60}")
            print(f"File: {filepath.name} ({len(cases)} cases)")
            print(f"{'='*60}")
            eval_results = evaluate(cases)
            print(json.dumps(eval_results, indent=2))

    else:
        if args.file:
            filepath = resolve_file(args.file)
        else:
            filepath = EVAL_CASES_DIR / "eval_cases_basic.json"

        cases = load_cases(filepath)
        print(f"Method: {settings.METHOD}")
        print(f"File: {filepath.name} ({len(cases)} cases)")
        eval_results = evaluate(cases)
        print(json.dumps(eval_results, indent=2))


if __name__ == "__main__":
    main()
