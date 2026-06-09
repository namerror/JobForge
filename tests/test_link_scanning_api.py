import asyncio

import httpx

from app.link_scanning.llm_client import LLMLinkScanResult, LinkScanningLLMClientError
from app.link_scanning.models import LinkScanHighlight
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
        "links": ["https://example.com/jobforge", "https://docs.example.com/jobforge"],
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


def test_scan_link_api_returns_llm_highlight_patch_with_details(monkeypatch):
    captured = {}

    def fake_scan_project_links_with_llm(**kwargs):
        captured.update(kwargs)
        return LLMLinkScanResult(
            highlights=[
                LinkScanHighlight(
                    text="Scanned page confirms grounded resume orchestration.",
                    source_url="https://example.com/jobforge",
                )
            ],
            metadata={
                "model": kwargs["model"],
                "api_calls": 1,
                "scanned_links": kwargs["project"].links,
                "source_urls": ["https://example.com/jobforge"],
                "total_tokens": 42,
            },
        )

    monkeypatch.setattr(
        "app.link_scanning.service.scan_project_links_with_llm",
        fake_scan_project_links_with_llm,
    )

    response = api_request("POST", "/scan-link", json=_request_payload())

    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == "jobforge"
    assert data["added_highlights"] == [
        {
            "text": "Scanned page confirms grounded resume orchestration.",
            "source_url": "https://example.com/jobforge",
        }
    ]
    assert "added_skills" not in data
    assert data["details"]["method"] == "llm"
    assert data["details"]["scanned_links"] == [
        "https://example.com/jobforge",
        "https://docs.example.com/jobforge",
    ]
    assert data["details"]["_link_scanning_llm"]["total_tokens"] == 42
    assert captured["context"].title == "Backend Engineer"
    assert captured["project"].id == "jobforge"


def test_scan_link_api_omits_details_when_dev_mode_false(monkeypatch):
    def fake_scan_project_links_with_llm(**_kwargs):
        return LLMLinkScanResult(
            highlights=[],
            metadata={"model": "test-model", "api_calls": 1, "total_tokens": 0},
        )

    monkeypatch.setattr(
        "app.link_scanning.service.scan_project_links_with_llm",
        fake_scan_project_links_with_llm,
    )

    response = api_request("POST", "/scan-link", json=_request_payload(dev_mode=False))

    assert response.status_code == 200
    assert response.json()["details"] is None


def test_scan_link_api_passes_llm_overrides(monkeypatch):
    captured = {}

    def fake_scan_project_links_with_llm(**kwargs):
        captured.update(kwargs)
        return LLMLinkScanResult(
            highlights=[],
            metadata={"model": kwargs["model"], "api_calls": 1, "total_tokens": 0},
        )

    monkeypatch.setattr(
        "app.link_scanning.service.scan_project_links_with_llm",
        fake_scan_project_links_with_llm,
    )

    response = api_request(
        "POST",
        "/scan-link",
        json=_request_payload(
            llm_model="request-link-model",
            llm_max_output_tokens=333,
        ),
    )

    assert response.status_code == 200
    assert captured["model"] == "request-link-model"
    assert captured["max_output_tokens"] == 333


def test_scan_link_api_returns_502_when_llm_fails(monkeypatch):
    def fake_scan_project_links_with_llm(**_kwargs):
        raise LinkScanningLLMClientError("web scan failed")

    monkeypatch.setattr(
        "app.link_scanning.service.scan_project_links_with_llm",
        fake_scan_project_links_with_llm,
    )

    response = api_request("POST", "/scan-link", json=_request_payload())

    assert response.status_code == 502
    assert "web scan failed" in response.text


def test_scan_link_api_rejects_unknown_project_skill_category():
    project = _project_payload()
    project["skills"]["design"] = ["UX"]

    response = api_request("POST", "/scan-link", json=_request_payload(project=project))

    assert response.status_code == 422
    assert "design" in response.text
