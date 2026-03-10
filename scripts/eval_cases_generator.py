"""Generate evaluation cases from skill pools.

Reads skill_pools.json and produces eval case files with randomized
skill mixes drawn from core/nice/exclude buckets.

Usage:
    python scripts/eval_cases_generator.py [OPTIONS]

Examples:
    python scripts/eval_cases_generator.py
    python scripts/eval_cases_generator.py --cases-per-role 10 --seed 42
    python scripts/eval_cases_generator.py --min-relevant 3 --max-relevant 6 --min-noise 1 --max-noise 3
    python scripts/eval_cases_generator.py --no-ranking
"""

import argparse
import json
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DEFAULT_POOLS = REPO_ROOT / "data" / "skill_pools" / "normalized" / "skill_pools.json"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "eval_cases" / "generated"

CATEGORIES = ["technology", "programming", "concepts"]

# Role name variants to add realism (whitespace, casing, hyphens)
ROLE_NAME_VARIANTS = {
    "backend": [
        "backend developer",
        "Backend Engineer",
        "back-end developer",
        "  Backend  Developer  ",
    ],
    "frontend": [
        "Frontend Engineer",
        "frontend developer",
        "front-end developer",
        "  Frontend  Developer  ",
    ],
    "fullstack": [
        "Full Stack Developer",
        "fullstack developer",
        "full-stack engineer",
        "Full Stack Engineer",
    ],
    "devops": [
        "DevOps Engineer",
        "devops engineer",
        "  DevOps  Engineer  ",
        "Dev Ops Engineer",
    ],
    "mobile": [
        "mobile developer",
        "Mobile Engineer",
        "mobile app developer",
    ],
    "data": [
        "data scientist",
        "Data Analyst",
        "data engineer",
        "Data Scientist",
    ],
    "security": [
        "Security Engineer",
        "Cyber Security Analyst",
        "security engineer",
    ],
    "ml": [
        "ML Engineer",
        "Machine Learning Engineer",
        "ml engineer",
        "ML/AI Engineer",
    ],
}

# Fallback: generate a simple variant from the role key
def _default_role_variants(role_key: str) -> list[str]:
    name = role_key.replace("_", " ").replace("-", " ")
    return [
        f"{name} developer",
        f"{name.title()} Engineer",
        f"  {name.title()}  Developer  ",
    ]


def load_skill_pools(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def sample_skills(
    pool: dict,
    category: str,
    min_relevant: int,
    max_relevant: int,
    min_noise: int,
    max_noise: int,
    rng: random.Random,
) -> tuple[list[str], list[str]]:
    """Sample relevant (core+nice) and noise (exclude) skills for a category.

    Returns (input_skills, expected_skills) where expected contains only
    the sampled relevant skills.
    """
    buckets = pool.get(category, {})
    core = list(buckets.get("core", []))
    nice = list(buckets.get("nice", []))
    exclude = list(buckets.get("exclude", []))

    relevant_pool = core + nice
    if not relevant_pool:
        return [], []

    # Determine how many to sample (clamped to available)
    n_relevant = rng.randint(min_relevant, max_relevant)
    n_relevant = min(n_relevant, len(relevant_pool))

    n_noise = rng.randint(min_noise, max_noise)
    n_noise = min(n_noise, len(exclude))

    sampled_relevant = rng.sample(relevant_pool, n_relevant)
    sampled_noise = rng.sample(exclude, n_noise) if n_noise > 0 else []

    input_skills = sampled_relevant + sampled_noise
    rng.shuffle(input_skills)

    return input_skills, sampled_relevant


def rank_expected(
    skills: list[str],
    pool: dict,
    category: str,
    ranking: bool,
) -> list[str]:
    """Order expected skills: core first, then nice, alphabetical within tier.

    If ranking is disabled, returns alphabetical order only.
    """
    if not ranking:
        return sorted(skills)

    buckets = pool.get(category, {})
    core_set = set(buckets.get("core", []))

    core_skills = sorted(s for s in skills if s in core_set)
    nice_skills = sorted(s for s in skills if s not in core_set)

    return core_skills + nice_skills


def generate_cases_for_role(
    role_key: str,
    pool: dict,
    cases_per_role: int,
    min_relevant: int,
    max_relevant: int,
    min_noise: int,
    max_noise: int,
    ranking: bool,
    rng: random.Random,
) -> list[dict]:
    """Generate N eval cases for a single role profile."""
    variants = ROLE_NAME_VARIANTS.get(role_key, _default_role_variants(role_key))
    cases = []

    for i in range(cases_per_role):
        job_role = variants[i % len(variants)]

        input_skills = {}
        expected_skills = {}

        for cat in CATEGORIES:
            input_list, relevant_list = sample_skills(
                pool, cat,
                min_relevant, max_relevant,
                min_noise, max_noise,
                rng,
            )
            input_skills[cat] = input_list
            expected_skills[cat] = rank_expected(relevant_list, pool, cat, ranking)

        case = {
            "input": {
                "job_role": job_role,
                **input_skills,
            },
            "expected": expected_skills,
        }
        cases.append(case)

    return cases


def generate_eval_cases(
    pools: dict,
    cases_per_role: int,
    min_relevant: int,
    max_relevant: int,
    min_noise: int,
    max_noise: int,
    ranking: bool,
    rng: random.Random,
) -> list[dict]:
    """Generate eval cases across all roles in the skill pools."""
    all_cases = []

    for role_key, pool in sorted(pools.items()):
        # Check that the role has at least one category with skills
        has_skills = any(
            pool.get(cat, {}).get("core") or pool.get(cat, {}).get("nice")
            for cat in CATEGORIES
        )
        if not has_skills:
            continue

        role_cases = generate_cases_for_role(
            role_key, pool,
            cases_per_role,
            min_relevant, max_relevant,
            min_noise, max_noise,
            ranking, rng,
        )
        all_cases.extend(role_cases)

    return all_cases


def build_output_path(output_dir: Path) -> Path:
    """Build a unique output filename with timestamp and short UUID."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    short_id = uuid.uuid4().hex[:8]
    filename = f"eval_cases_{timestamp}_{short_id}.json"
    return output_dir / filename


def main():
    parser = argparse.ArgumentParser(
        description="Generate eval cases from skill pools.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--pools", type=Path, default=DEFAULT_POOLS,
        help="Path to skill_pools.json (default: data/skill_pools/normalized/skill_pools.json)",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
        help="Directory for generated eval case files (default: data/eval_cases/generated/)",
    )
    parser.add_argument(
        "--cases-per-role", type=int, default=5,
        help="Number of eval cases to generate per role profile (default: 5)",
    )
    parser.add_argument(
        "--min-relevant", type=int, default=3,
        help="Minimum relevant skills (core+nice) to sample per category (default: 3)",
    )
    parser.add_argument(
        "--max-relevant", type=int, default=7,
        help="Maximum relevant skills (core+nice) to sample per category (default: 7)",
    )
    parser.add_argument(
        "--min-noise", type=int, default=1,
        help="Minimum noise (exclude) skills to sample per category (default: 1)",
    )
    parser.add_argument(
        "--max-noise", type=int, default=3,
        help="Maximum noise (exclude) skills to sample per category (default: 3)",
    )
    parser.add_argument(
        "--ranking", action=argparse.BooleanOptionalAction, default=True,
        help="Rank expected output: core before nice, alphabetical within tier (default: true). Use --no-ranking to disable.",
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for reproducible generation (default: None = non-deterministic)",
    )

    args = parser.parse_args()

    rng = random.Random(args.seed)
    pools = load_skill_pools(args.pools)

    cases = generate_eval_cases(
        pools,
        cases_per_role=args.cases_per_role,
        min_relevant=args.min_relevant,
        max_relevant=args.max_relevant,
        min_noise=args.min_noise,
        max_noise=args.max_noise,
        ranking=args.ranking,
        rng=rng,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = build_output_path(args.output_dir)

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "cases_per_role": args.cases_per_role,
        "min_relevant": args.min_relevant,
        "max_relevant": args.max_relevant,
        "min_noise": args.min_noise,
        "max_noise": args.max_noise,
        "ranking": args.ranking,
        "roles": sorted(pools.keys()),
        "total_cases": len(cases),
    }

    output = {
        "metadata": metadata,
        "cases": cases,
    }

    output_path.write_text(json.dumps(output, indent=2) + "\n")

    print(f"Generated {len(cases)} eval cases")
    print(f"  Roles: {', '.join(sorted(pools.keys()))}")
    print(f"  Cases per role: {args.cases_per_role}")
    print(f"  Seed: {args.seed}")
    print(f"  Ranking: {args.ranking}")
    print(f"  Output: {output_path}")


if __name__ == "__main__":
    main()
