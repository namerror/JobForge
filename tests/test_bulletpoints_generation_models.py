import pytest
from pydantic import ValidationError

from app.bulletpoints_generation.models import (
    BulletCountRange,
    BulletGenerationRequest,
    BulletJobContext,
)
from app.bulletpoints_generation.service import effective_bullet_count_range


def _project_payload(**overrides):
    payload = {
        "id": "jobforge",
        "name": "JobForge",
        "summary": "Resume engine for grounded, job-targeted resume generation.",
        "highlights": [
            "Built a FastAPI service for deterministic skill and project selection.",
            "Added grounded project evidence parsing and validation.",
        ],
        "active": True,
        "skills": {
            "technology": ["FastAPI", "OpenAI"],
            "programming": ["Python"],
            "concepts": ["API", "Resume Generation"],
        },
        "links": ["https://example.com/jobforge"],
    }
    payload.update(overrides)
    return payload


def test_bullet_count_range_accepts_exact_and_flexible_ranges():
    exact = BulletCountRange(min=3, max=3)
    flexible = BulletCountRange(min=2, max=4)

    assert exact.min == exact.max == 3
    assert flexible.min == 2
    assert flexible.max == 4


@pytest.mark.parametrize(
    "count_range",
    [
        {"min": 0, "max": 3},
        {"min": 3, "max": 11},
        {"min": 4, "max": 3},
    ],
)
def test_bullet_count_range_rejects_invalid_ranges(count_range):
    with pytest.raises(ValidationError):
        BulletCountRange.model_validate(count_range)


def test_bullet_generation_request_accepts_full_project_record():
    request = BulletGenerationRequest.model_validate(
        {
            "context": {"title": "Backend Engineer", "description": "Build Python APIs."},
            "project": _project_payload(),
            "bullet_count_range": {"min": 2, "max": 4},
            "dev_mode": True,
        }
    )

    assert request.context.title == "Backend Engineer"
    assert request.project.highlights[0].startswith("Built a FastAPI")
    assert request.bullet_count_range is not None
    assert request.bullet_count_range.max == 4


def test_bullet_generation_request_rejects_empty_title():
    with pytest.raises(ValidationError, match="title"):
        BulletJobContext(title="  ")


def test_bullet_generation_request_rejects_extra_project_fields():
    project = _project_payload(extra_claim="invented")

    with pytest.raises(ValidationError, match="extra_claim"):
        BulletGenerationRequest.model_validate(
            {
                "context": {"title": "Backend Engineer"},
                "project": project,
            }
        )


def test_effective_bullet_count_range_uses_config_default(monkeypatch):
    from app.bulletpoints_generation import service

    monkeypatch.setattr(service.settings, "BULLETPOINTS_DEFAULT_COUNT", 5)

    count_range = effective_bullet_count_range(None)

    assert count_range.min == 5
    assert count_range.max == 5
