import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import App from "./App";
import type { EvidenceApi } from "./api";
import { cloneEvidence } from "./draft";
import { sampleEvidence } from "./testFixtures";

describe("App", () => {
  it("stages user edits and applies them through the user endpoint", async () => {
    const evidence = sampleEvidence();
    const reloaded = cloneEvidence(evidence);
    reloaded.user.email = "updated@example.com";
    const client = createMockClient(evidence, reloaded);

    render(<App client={client} />);

    const emailInput = (await screen.findByLabelText("Email")) as HTMLInputElement;
    fireEvent.change(emailInput, { target: { value: "updated@example.com" } });

    const applyButton = screen.getByRole("button", { name: /apply/i }) as HTMLButtonElement;
    expect(applyButton.disabled).toBe(false);
    fireEvent.click(applyButton);

    await waitFor(() => {
      expect(client.updateUser).toHaveBeenCalledWith({
        name: "Example Candidate",
        email: "updated@example.com",
        phone: "+1 555-0100",
        linkedin: "https://www.linkedin.com/in/example-candidate",
        github: "https://github.com/example-candidate",
        website: null,
      });
    });
    expect(client.getResumeEvidence).toHaveBeenCalledTimes(2);
  });

  it("keeps new projects local until Apply is clicked", async () => {
    const evidence = sampleEvidence();
    const reloaded = cloneEvidence(evidence);
    reloaded.projects.projects.push({
      id: "portfolio-api",
      name: "Portfolio API",
      summary: "FastAPI portfolio service.",
      highlights: ["Built staged CRUD workflows."],
      active: true,
      skills: {
        technology: [],
        programming: [],
        concepts: [],
      },
      links: null,
    });
    const client = createMockClient(evidence, reloaded);

    render(<App client={client} />);

    fireEvent.click(await screen.findByRole("button", { name: "Projects" }));
    fireEvent.click(screen.getByRole("button", { name: "Add Project" }));
    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Portfolio API" } });
    fireEvent.change(screen.getByLabelText("Summary"), {
      target: { value: "FastAPI portfolio service." },
    });
    fireEvent.change(screen.getByLabelText("Highlights 1"), {
      target: { value: "Built staged CRUD workflows." },
    });

    expect(client.createProject).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: /apply/i }));

    await waitFor(() => {
      expect(client.createProject).toHaveBeenCalledWith({
        name: "Portfolio API",
        summary: "FastAPI portfolio service.",
        highlights: ["Built staged CRUD workflows."],
        active: true,
        skills: {
          technology: [],
          programming: [],
          concepts: [],
        },
        links: null,
      });
    });
  });

  it("keeps project deletes local until Apply is clicked", async () => {
    const evidence = sampleEvidence();
    const reloaded = cloneEvidence(evidence);
    reloaded.projects.projects = [];
    const client = createMockClient(evidence, reloaded);

    render(<App client={client} />);

    fireEvent.click(await screen.findByRole("button", { name: "Projects" }));
    fireEvent.click(screen.getByLabelText("Delete JobForge"));

    expect(client.deleteProject).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: /apply/i }));

    await waitFor(() => {
      expect(client.deleteProject).toHaveBeenCalledWith("jobforge");
    });
  });
});

function createMockClient(
  initial = sampleEvidence(),
  reloaded = initial,
): EvidenceApi & Record<string, ReturnType<typeof vi.fn>> {
  return {
    getHealth: vi.fn().mockResolvedValue({ status: "ok" }),
    getResumeEvidence: vi
      .fn()
      .mockResolvedValueOnce(cloneEvidence(initial))
      .mockResolvedValue(cloneEvidence(reloaded)),
    getProjects: vi.fn(),
    createProject: vi.fn().mockResolvedValue(reloaded.projects.projects.at(-1)),
    updateProject: vi.fn(),
    deleteProject: vi.fn().mockResolvedValue(initial.projects.projects[0]),
    getExperience: vi.fn(),
    createExperience: vi.fn(),
    updateExperience: vi.fn(),
    deleteExperience: vi.fn(),
    getEducation: vi.fn(),
    createEducation: vi.fn(),
    updateEducation: vi.fn(),
    deleteEducation: vi.fn(),
    updateSkills: vi.fn(),
    updateUser: vi.fn().mockResolvedValue(reloaded.user),
  };
}
