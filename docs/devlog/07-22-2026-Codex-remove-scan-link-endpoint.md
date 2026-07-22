### 2026-07-22 - Remove Legacy Scan Link Endpoint

**Agent:** Codex (GPT-5)

**Changes:**
- `app/main.py` - Removed the duplicate `POST /scan-link` route while keeping `POST /enrich-link-evidence` as the canonical link enrichment API.
- `app/link_scanning/models.py` - Removed the legacy project/context payload adapter from `LinkScanRequest`.
- `tests/test_link_scanning_api.py` - Updated endpoint coverage for canonical enrichment requests, removed legacy compatibility expectations, and added `/scan-link` removal coverage.
- `README.md` and `docs/architecture-overview.md` - Updated active API documentation to list only `/enrich-link-evidence` for link evidence enrichment.
- `docs/decisions/014-canonical-link-evidence-enrichment-endpoint.md` - Recorded the endpoint consolidation decision.

**Rationale:**
`/scan-link` and `/enrich-link-evidence` were semantically equivalent and both called the same service. The repo had no active production or orchestration callers for `/scan-link`; keeping the alias and legacy project-only payload compatibility made the internal API boundary less clear.

**Tests:**
- `test_scan_link_api_is_removed`: validates `POST /scan-link` is no longer registered.
- `test_enrich_link_evidence_api_rejects_legacy_project_payload`: validates the canonical endpoint rejects the removed legacy request shape.
- Existing link enrichment API tests continue to validate project and experience evidence scanning behavior.

**Impact:**
Link evidence enrichment now has one backend HTTP contract. Future clients and docs can target `POST /enrich-link-evidence` without carrying the older project-only route or payload shape forward.
