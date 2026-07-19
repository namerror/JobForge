import pytest

from app.skill_selection.scoring import llm
from app.skill_selection.scoring.baseline import baseline_select_skills
from app.skill_selection.scoring.llm import llm_select_skills
from app.skill_selection.llm_client import LLMClientError, LLMScoreResult


def _llm_result(scores):
    return LLMScoreResult(
        scores=scores,
        metadata={
            "model": "test-model",
            "api_calls": 1,
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
            "latency_ms": 1.23,
        },
    )


def test_llm_select_skills_ranks_locally_with_normalized_tiebreak(monkeypatch):
    monkeypatch.setattr(
        llm,
        "score_skills_with_llm",
        lambda **_kwargs: _llm_result(
            {
                "technology": {"Zebra": 2, "Alpha": 2, "React": 3},
                "programming": {"JS": 2, "Python": 2},
                "concepts": {"UX": 1},
            }
        ),
    )

    selected, details = llm_select_skills(
        job_role="Frontend Engineer",
        technology=["Zebra", "Alpha", "React"],
        programming=["Python", "JS"],
        concepts=["UX"],
        top_n=2,
        dev_mode=True,
    )

    assert selected["technology"] == ["React", "Alpha"]
    assert selected["programming"] == ["JS", "Python"]
    assert selected["concepts"] == ["UX"]
    assert details["_llm"]["model"] == "test-model"
    assert details["programming"]["JS"]["normalized_skill"] == "javascript"


def test_llm_select_skills_discards_invented_skills_and_unknown_categories(monkeypatch):
    monkeypatch.setattr(
        llm,
        "score_skills_with_llm",
        lambda **_kwargs: _llm_result(
            {
                "technology": {"React": 3, "InventedDB": 3},
                "programming": {"JavaScript": 2},
                "concepts": {"UI": 2},
                "other": {"NotACategory": 3},
            }
        ),
    )

    selected, details = llm_select_skills(
        job_role="Frontend Engineer",
        technology=["React"],
        programming=["JavaScript"],
        concepts=["UI"],
        dev_mode=True,
    )

    assert selected == {
        "technology": ["React"],
        "programming": ["JavaScript"],
        "concepts": ["UI"],
    }
    assert "InventedDB" not in selected["technology"]
    assert any("InventedDB" in warning for warning in details["_warnings"])


def test_llm_select_skills_discards_invalid_scores(monkeypatch):
    monkeypatch.setattr(
        llm,
        "score_skills_with_llm",
        lambda **_kwargs: _llm_result(
            {
                "technology": {"React": 3, "Vue": 4, "Angular": "3", "Svelte": True},
                "programming": {"JavaScript": 2},
                "concepts": {"UI": 2},
            }
        ),
    )

    selected, details = llm_select_skills(
        job_role="Frontend Engineer",
        technology=["React", "Vue", "Angular", "Svelte"],
        programming=["JavaScript"],
        concepts=["UI"],
        dev_mode=True,
    )

    assert selected["technology"] == ["React"]
    assert len(details["_warnings"]) == 3


def test_llm_select_skills_missing_category_falls_back_to_baseline(monkeypatch):
    monkeypatch.setattr(
        llm,
        "score_skills_with_llm",
        lambda **_kwargs: _llm_result(
            {
                "technology": {"Django": 3},
                "programming": {"Python": 3},
            }
        ),
    )

    selected, details = llm_select_skills(
        job_role="Backend Engineer",
        technology=["Django"],
        programming=["Python"],
        concepts=["API"],
        top_n=1,
        dev_mode=True,
    )
    expected, _ = baseline_select_skills(
        job_role="Backend Engineer",
        technology=["Django"],
        programming=["Python"],
        concepts=["API"],
        top_n=1,
        dev_mode=True,
    )

    assert selected == expected
    assert details["_llm"]["fallback"] == "baseline"
    assert details["_llm"]["total_tokens"] == 15
    assert any("fell back to baseline" in warning for warning in details["_warnings"])


def test_llm_select_skills_client_failure_falls_back_to_baseline(monkeypatch):
    def raise_client_error(**_kwargs):
        raise LLMClientError(
            "bad response",
            metadata={
                "model": "test-model",
                "api_calls": 2,
                "prompt_tokens": 20,
                "completion_tokens": 12,
                "total_tokens": 32,
                "attempts": [
                    {"attempt": 1, "max_output_tokens": 1200, "total_tokens": 20},
                    {"attempt": 2, "max_output_tokens": 3000, "total_tokens": 12},
                ],
            },
        )

    monkeypatch.setattr(llm, "score_skills_with_llm", raise_client_error)

    selected, details = llm_select_skills(
        job_role="Backend Engineer",
        technology=["Django"],
        programming=["Python"],
        concepts=["API"],
        top_n=1,
        dev_mode=True,
    )
    expected, _ = baseline_select_skills(
        job_role="Backend Engineer",
        technology=["Django"],
        programming=["Python"],
        concepts=["API"],
        top_n=1,
        dev_mode=True,
    )

    assert selected == expected
    assert details["_llm"]["reason"].endswith("bad response")
    assert details["_llm"]["total_tokens"] == 32
    assert [attempt["max_output_tokens"] for attempt in details["_llm"]["attempts"]] == [
        1200,
        3000,
    ]


def test_llm_fallback_fills_top_n_with_zero_score_skills(monkeypatch):
    def raise_client_error(**_kwargs):
        raise LLMClientError("bad response", metadata={"total_tokens": 1})

    monkeypatch.setattr(llm, "score_skills_with_llm", raise_client_error)

    selected, details = llm_select_skills(
        job_role="Backend Engineer",
        technology=["Django", "Photoshop", "Blender"],
        programming=["Python", "COBOL", "Logo"],
        concepts=["API", "Branding", "Animation"],
        top_n=3,
        dev_mode=True,
    )

    assert selected == {
        "technology": ["Django", "Blender", "Photoshop"],
        "programming": ["Python", "COBOL", "Logo"],
        "concepts": ["API", "Animation", "Branding"],
    }
    assert details["technology"]["Photoshop"]["score"] == 0.0
    assert details["_fallback_method"] == "baseline"


def test_llm_select_skills_top_n_after_validation(monkeypatch):
    monkeypatch.setattr(
        llm,
        "score_skills_with_llm",
        lambda **_kwargs: _llm_result(
            {
                "technology": {"React": 3, "Vue": 3, "Invented": 3, "Angular": 2},
                "programming": {},
                "concepts": {},
            }
        ),
    )

    selected, _ = llm_select_skills(
        job_role="Frontend Engineer",
        technology=["Vue", "Angular", "React"],
        programming=[],
        concepts=[],
        top_n=2,
    )

    assert selected["technology"] == ["React", "Vue"]
