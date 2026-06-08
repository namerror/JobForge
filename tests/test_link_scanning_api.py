import asyncio

import httpx

from app.main import app


def api_request(method: str, path: str, **kwargs):
    async def _request():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(_request())


def _project_payload() -> dict:
    return {
        "id": "jobforge",
        "name": "JobForge",
        "summary": "FastAPI resume engine for grounded resume generation.",
        "highlights": ["Built project and skill selection APIs."],
        "active": True,
        "skills": {
            "technology": ["FastAPI"],
            "programming": ["Python"],
            "concepts": ["API"],
        },
        "links": ["https://example.com/jobforge"],
    }


def _request_payload(**overrides) -> dict:
    payload = {
        "context": {
            "title": "Backend Engineer",
            "description": "Build Python APIs with grounded AI workflows.",
        },
        "project": _project_payload(),
        "dev_mode": True,
    }
    payload.update(overrides)
    return payload


def test_scan_link_api_returns_placeholder_patch_with_details():
    response = api_request("POST", "/scan-link", json=_request_payload())

    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == "jobforge"
    assert data["added_highlights"] == []
    assert data["added_skills"] == []
    assert data["details"]["method"] == "placeholder"
    assert data["details"]["scanned_links"] == []


def test_scan_link_api_omits_details_when_dev_mode_false():
    response = api_request("POST", "/scan-link", json=_request_payload(dev_mode=False))

    assert response.status_code == 200
    assert response.json()["details"] is None


def test_scan_link_api_rejects_unknown_project_skill_category():
    project = _project_payload()
    project["skills"]["design"] = ["UX"]

    response = api_request("POST", "/scan-link", json=_request_payload(project=project))

    assert response.status_code == 422
    assert "design" in response.text
