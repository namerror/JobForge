from __future__ import annotations

from app.link_scanning.models import LinkScanRequest, LinkScanResponse


def scan_project_links_service(req: LinkScanRequest) -> LinkScanResponse:
    details = None
    if req.dev_mode:
        details = {
            "method": "placeholder",
            "scanned_links": [],
            "skipped_reason": "link scanning implementation is not wired yet",
        }

    return LinkScanResponse(
        project_id=req.project.id,
        added_highlights=[],
        added_skills=[],
        details=details,
    )

