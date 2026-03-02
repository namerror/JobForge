"""Build skill_pools.json from raw skill pool text files.

Usage:
    python scripts/build_skill_pools.py [--raw-dir PATH] [--output PATH]

Reads raw/<role>/<category>.txt files and writes normalized/skill_pools.json.
"""

import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DEFAULT_RAW_DIR = REPO_ROOT / "data" / "skill_pools" / "raw"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "skill_pools" / "normalized" / "skill_pools.json"

SECTION_RE = re.compile(r"^\[(\w+)\]$")


def parse_raw_file(path: Path) -> dict[str, list[str]]:
    """Parse a single raw skill pool file into a dict of bucket -> skill list."""
    buckets: dict[str, list[str]] = {}
    current_bucket: str | None = None
    accumulated: list[str] = []

    def flush():
        if current_bucket is not None:
            raw = ",".join(accumulated)
            skills = [s.strip() for s in raw.split(",") if s.strip()]
            buckets[current_bucket] = skills

    for line in path.read_text().splitlines():
        line = line.strip()
        m = SECTION_RE.match(line)
        if m:
            flush()
            current_bucket = m.group(1)
            accumulated = []
        elif current_bucket is not None and line:
            accumulated.append(line)

    flush()
    return buckets


def build_skill_pools(raw_dir: Path) -> dict:
    """Walk raw_dir and build the nested skill pools structure."""
    result: dict = {}

    for role_dir in sorted(raw_dir.iterdir()):
        if not role_dir.is_dir():
            continue
        role = role_dir.name
        result[role] = {}

        for cat_file in sorted(role_dir.glob("*.txt")):
            category = cat_file.stem
            result[role][category] = parse_raw_file(cat_file)

    return result


def print_summary(pools: dict) -> None:
    for role, categories in pools.items():
        print(f"\n{role}:")
        for category, buckets in categories.items():
            counts = {b: len(skills) for b, skills in buckets.items()}
            counts_str = ", ".join(f"{b}={n}" for b, n in counts.items())
            print(f"  {category}: {counts_str}")


def main():
    parser = argparse.ArgumentParser(description="Build skill_pools.json from raw files.")
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    pools = build_skill_pools(args.raw_dir)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(pools, indent=2, sort_keys=True) + "\n")

    print(f"Written to {args.output}")
    print_summary(pools)


if __name__ == "__main__":
    main()
