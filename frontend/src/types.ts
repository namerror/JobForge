export const skillCategories = ["technology", "programming", "concepts"] as const;

export type SkillCategory = (typeof skillCategories)[number];

export interface ProjectSkills {
  technology: string[];
  programming: string[];
  concepts: string[];
}

export interface ProjectRecordInput {
  name: string;
  summary: string;
  highlights: string[];
  active: boolean;
  skills: ProjectSkills;
  links: string[] | null;
}

export interface ProjectRecord extends ProjectRecordInput {
  id: string;
}

export interface ProjectsFile {
  schema_version: 1;
  projects: ProjectRecord[];
}

export interface ExperienceRecordInput {
  name: string;
  role: string;
  summary: string;
  highlights: string[];
  active: boolean;
  skills: ProjectSkills;
  location: string;
  start: string;
  end: string | null;
  links: string[] | null;
}

export interface ExperienceRecord extends ExperienceRecordInput {
  id: string;
}

export interface ExperienceFile {
  schema_version: 1;
  experience: ExperienceRecord[];
}

export interface EducationRecordInput {
  name: string;
  degree: string;
  grade: string;
  start: string;
  end: string | null;
  location: string;
  relevant_coursework: string[];
}

export interface EducationRecord extends EducationRecordInput {
  id: string;
}

export interface EducationFile {
  schema_version: 1;
  education: EducationRecord[];
}

export interface SkillsFile {
  schema_version: 1;
  skills: ProjectSkills;
}

export interface SkillsInput {
  skills: ProjectSkills;
}

export interface UserInfoInput {
  name: string;
  email: string;
  phone: string;
  linkedin: string | null;
  github: string | null;
  website: string | null;
}

export interface UserInfoFile extends UserInfoInput {
  schema_version: 1;
}

export interface ResumeEvidenceRegistry {
  education: EducationFile;
  experience: ExperienceFile;
  projects: ProjectsFile;
  skills: SkillsFile;
  user: UserInfoFile;
}

export type CollectionRecord = ProjectRecord | ExperienceRecord | EducationRecord;
