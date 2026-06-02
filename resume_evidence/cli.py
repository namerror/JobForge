from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable, TextIO

from resume_evidence.session import (
    ProjectsEvidenceSession,
    SkillsEvidenceSession,
)

from resume_evidence.skills_cli import SkillsEvidenceCLI
from resume_evidence.projects_cli import ProjectsEvidenceCLI


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Interactive CLI for resume evidence.")
    parser.add_argument(
        "--path",
        type=Path,
        default=None,
        help="Optional path to an evidence YAML file. Defaults to the selected user/resume_evidence file.",
    )
    parser.add_argument(
        "--schema",
        choices=("projects", "skills"),
        default="projects",
        help="Evidence schema to manage. Defaults to projects.",
    )
    return parser

def main(
    argv: list[str] | None = None,
    *,
    input_func: Callable[[str], str] = input,
    output: TextIO | None = None,
) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.schema == "skills":
        session = SkillsEvidenceSession.load(args.path)
        cli = SkillsEvidenceCLI(session, input_func=input_func, output=output)
    else:
        session = ProjectsEvidenceSession.load(args.path)
        cli = ProjectsEvidenceCLI(session, input_func=input_func, output=output)

    return cli.run()


if __name__ == "__main__":
    raise SystemExit(main())
