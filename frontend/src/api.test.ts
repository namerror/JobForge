import { describe, expect, it, vi } from "vitest";

import { ApiError, createEvidenceApi } from "./api";

describe("evidence api client", () => {
  it("updates project records through the ID route with an ID-free payload", async () => {
    const payload = {
      name: "JobForge",
      summary: "Updated summary.",
      highlights: ["Built APIs."],
      active: true,
      skills: {
        technology: ["FastAPI"],
        programming: ["Python"],
        concepts: ["API"],
      },
      links: null,
    };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue({ id: "jobforge", ...payload }),
    });
    const api = createEvidenceApi({
      baseUrl: "http://127.0.0.1:8000",
      fetchImpl: fetchMock as unknown as typeof fetch,
    });

    await api.updateProject("jobforge", payload);

    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/resume-evidence/projects/jobforge",
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify(payload),
      }),
    );
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).not.toHaveProperty("id");
  });

  it("surfaces FastAPI error details", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      statusText: "Bad Request",
      json: vi.fn().mockResolvedValue({ detail: "invalid evidence" }),
    });
    const api = createEvidenceApi({
      baseUrl: "/api",
      fetchImpl: fetchMock as unknown as typeof fetch,
    });

    await expect(api.getResumeEvidence()).rejects.toEqual(new ApiError(400, "invalid evidence"));
  });
});
