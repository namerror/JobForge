import type { ResumeEvidenceRegistry } from "./types";

export function validateDraftEvidence(draft: ResumeEvidenceRegistry): string[] {
  const errors: string[] = [];

  requireText(errors, "User name", draft.user.name);
  requireText(errors, "User email", draft.user.email);
  requireText(errors, "User phone", draft.user.phone);
  validateOptionalLinks(errors, "User links", [
    draft.user.linkedin,
    draft.user.github,
    draft.user.website,
  ]);
  validateList(errors, "Skills technology", draft.skills.skills.technology);
  validateList(errors, "Skills programming", draft.skills.skills.programming);
  validateList(errors, "Skills concepts", draft.skills.skills.concepts);

  for (const project of draft.projects.projects) {
    const label = project.name.trim() || "Untitled project";
    requireText(errors, `${label} name`, project.name);
    requireText(errors, `${label} summary`, project.summary);
    validateList(errors, `${label} highlights`, project.highlights, 1);
    validateList(errors, `${label} technology skills`, project.skills.technology);
    validateList(errors, `${label} programming skills`, project.skills.programming);
    validateList(errors, `${label} concept skills`, project.skills.concepts);
    validateList(errors, `${label} links`, project.links ?? []);
  }

  for (const experience of draft.experience.experience) {
    const label = experience.name.trim() || "Untitled experience";
    requireText(errors, `${label} organization`, experience.name);
    requireText(errors, `${label} role`, experience.role);
    requireText(errors, `${label} summary`, experience.summary);
    requireText(errors, `${label} location`, experience.location);
    requireText(errors, `${label} start`, experience.start);
    validateList(errors, `${label} highlights`, experience.highlights, 1);
    validateList(errors, `${label} technology skills`, experience.skills.technology);
    validateList(errors, `${label} programming skills`, experience.skills.programming);
    validateList(errors, `${label} concept skills`, experience.skills.concepts);
    validateList(errors, `${label} links`, experience.links ?? []);
  }

  for (const education of draft.education.education) {
    const label = education.name.trim() || "Untitled education";
    requireText(errors, `${label} institution`, education.name);
    requireText(errors, `${label} degree`, education.degree);
    requireText(errors, `${label} grade`, education.grade);
    requireText(errors, `${label} location`, education.location);
    requireText(errors, `${label} start`, education.start);
    validateList(errors, `${label} coursework`, education.relevant_coursework);
  }

  return errors;
}

function requireText(errors: string[], label: string, value: string): void {
  if (!value.trim()) {
    errors.push(`${label} is required.`);
  }
}

function validateList(
  errors: string[],
  label: string,
  values: string[],
  minLength = 0,
): void {
  if (values.length < minLength) {
    errors.push(`${label} needs at least ${minLength} entry.`);
  }
  if (values.some((value) => !value.trim())) {
    errors.push(`${label} has a blank entry.`);
  }
}

function validateOptionalLinks(errors: string[], label: string, values: Array<string | null>): void {
  if (values.some((value) => value !== null && !value.trim())) {
    errors.push(`${label} have a blank entry.`);
  }
}
