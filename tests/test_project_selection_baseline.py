from __future__ import annotations

import pytest

from app.project_selection import ProjectCandidate, ProjectJobContext, select_projects
from app.project_selection.baseline import score_project_baseline
from app.resume_evidence.models import ProjectSkills


def _candidate(
    project_id: str,
    name: str,
    summary: str = "",
    *,
    technology: list[str] | None = None,
    programming: list[str] | None = None,
    concepts: list[str] | None = None,
) -> ProjectCandidate:
    return ProjectCandidate(
        id=project_id,
        name=name,
        summary=summary,
        skills=ProjectSkills(
            technology=technology or [],
            programming=programming or [],
            concepts=concepts or [],
        ),
    )


def test_baseline_project_selection_is_skill_heavy_over_text_overlap():
    context = ProjectJobContext(
        title="Backend Engineer",
        description="Build Python Django APIs with PostgreSQL and authentication.",
    )
    skill_match = _candidate(
        "skill-match",
        "Skill Match",
        summary="A compact backend tool.",
        technology=["Django", "PostgreSQL"],
        programming=["Python"],
        concepts=["API"],
    )
    text_only = _candidate(
        "text-only",
        "Text Only",
        summary="Build Python Django APIs with PostgreSQL authentication for backend engineers.",
        technology=["React"],
        programming=["JavaScript"],
        concepts=["UX"],
    )

    result = select_projects(
        context=context,
        candidates=[text_only, skill_match],
        method="baseline",
        dev_mode=True,
    )

    assert result.selected_project_ids[0] == "skill-match"
    assert result.details["projects"]["skill-match"]["skill_score"] > 0
    assert result.details["projects"]["text-only"]["skill_score"] == 0


def test_baseline_project_selection_top_match_aggregation_ignores_extra_irrelevant_skills():
    context = ProjectJobContext(
        title="Backend Engineer",
        description="Python Django PostgreSQL Docker API authentication",
    )
    focused = _candidate(
        "focused",
        "Focused",
        technology=["Django", "PostgreSQL", "Docker"],
        programming=["Python"],
        concepts=["API"],
    )
    broad = _candidate(
        "broad",
        "Broad",
        technology=["Django", "PostgreSQL", "Docker", "React", "Unreal Engine"],
        programming=["Python", "Swift", "Kotlin"],
        concepts=["API", "Animation", "Game Design"],
    )

    focused_score = score_project_baseline(context=context, candidate=focused)
    broad_score = score_project_baseline(context=context, candidate=broad)

    assert focused_score.skill_score == broad_score.skill_score
    assert focused_score.considered_skill_count == 5
    assert broad_score.considered_skill_count == 5


def test_baseline_project_selection_tie_breaking_is_deterministic():
    context = ProjectJobContext(title="Backend Engineer", description=None)
    beta = _candidate("beta", "Beta")
    alpha = _candidate("alpha", "Alpha")

    result = select_projects(
        context=context,
        candidates=[beta, alpha],
        method="baseline",
    )

    assert result.selected_project_ids == ["alpha", "beta"]


def test_baseline_project_selection_handles_empty_skills_and_summary():
    context = ProjectJobContext(title="Backend Engineer", description="")
    empty = _candidate("empty", "Empty", summary="")

    result = select_projects(
        context=context,
        candidates=[empty],
        method="baseline",
        dev_mode=True,
    )

    assert result.selected_project_ids == ["empty"]
    assert result.ranked_projects[0].score == 0
    assert result.details["projects"]["empty"]["text_overlap_score"] == 0
    assert result.details["projects"]["empty"]["skill_score"] == 0


def test_project_selection_rejects_duplicate_project_ids():
    context = ProjectJobContext(title="Backend Engineer")
    first = _candidate("same-id", "First")
    second = _candidate("same-id", "Second")

    with pytest.raises(ValueError, match="Duplicate project ids"):
        select_projects(context=context, candidates=[first, second], method="baseline")


def test_project_selection_applies_top_n_after_ranking():
    context = ProjectJobContext(title="Backend Engineer", description="Python Django API")
    best = _candidate("best", "Best", technology=["Django"], programming=["Python"])
    middle = _candidate("middle", "Middle", concepts=["API"])
    low = _candidate("low", "Low")

    result = select_projects(
        context=context,
        candidates=[low, middle, best],
        method="baseline",
        top_n=2,
    )

    assert result.selected_project_ids == ["best", "middle"]
    assert [ranked.project_id for ranked in result.ranked_projects] == ["best", "middle"]


def test_project_selection_result_does_not_emit_project_content():
    context = ProjectJobContext(title="Backend Engineer")
    candidate = _candidate(
        "project",
        "Project",
        summary="Do not emit this project summary.",
        programming=["Python"],
    )

    result = select_projects(
        context=context,
        candidates=[candidate],
        method="baseline",
    )

    dumped = result.model_dump()
    assert dumped["selected_project_ids"] == ["project"]
    assert "Do not emit this project summary." not in str(dumped)
