import asyncio
import re
from pathlib import Path

import httpx

from app import __version__
from app.main import app


RELEASE_HEADING_RE = re.compile(r"^## \[(?P<version>\d+\.\d+\.\d+)\] - (?P<date>\d{4}-\d{2}-\d{2})$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def api_request(method: str, path: str, **kwargs):
    async def _request():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(_request())


def released_changelog_versions() -> list[str]:
    changelog = Path("docs/CHANGELOG.md").read_text(encoding="utf-8")
    return [
        match.group("version")
        for line in changelog.splitlines()
        if (match := RELEASE_HEADING_RE.match(line))
    ]


def test_version_constant_uses_semver():
    assert SEMVER_RE.fullmatch(__version__)


def test_health_reports_package_version():
    response = api_request("GET", "/health")

    assert response.status_code == 200
    assert response.json()["version"] == __version__


def test_changelog_contains_current_release_section():
    released_versions = released_changelog_versions()

    assert released_versions[0] == __version__
