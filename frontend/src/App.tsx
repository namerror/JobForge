import {
  AlertCircle,
  BriefcaseBusiness,
  CheckCircle2,
  FolderKanban,
  GraduationCap,
  Loader2,
  Plus,
  RefreshCw,
  RotateCcw,
  Save,
  Search,
  Trash2,
  UserRound,
  Wrench,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import type { EvidenceApi } from "./api";
import { ApiError, evidenceApi } from "./api";
import {
  applyEvidenceChanges,
  describeOperation,
} from "./diff";
import {
  cloneEvidence,
  createBlankEducation,
  createBlankExperience,
  createBlankProject,
  hasDraftChanges,
  isTempId,
} from "./draft";
import type {
  CollectionRecord,
  EducationRecord,
  ExperienceRecord,
  ProjectRecord,
  ProjectSkills,
  ResumeEvidenceRegistry,
  SkillCategory,
} from "./types";
import { skillCategories } from "./types";
import { validateDraftEvidence } from "./validation";

type SectionKey = "user" | "skills" | "experience" | "projects" | "education";
type BackendStatus = "checking" | "online" | "offline";

interface AppProps {
  client?: EvidenceApi;
}

interface SelectedIds {
  projects?: string;
  experience?: string;
  education?: string;
}

const sectionDefinitions: Array<{
  key: SectionKey;
  label: string;
  icon: LucideIcon;
}> = [
  { key: "user", label: "User", icon: UserRound },
  { key: "skills", label: "Skills", icon: Wrench },
  { key: "experience", label: "Experience", icon: BriefcaseBusiness },
  { key: "projects", label: "Projects", icon: FolderKanban },
  { key: "education", label: "Education", icon: GraduationCap },
];

const categoryLabels: Record<SkillCategory, string> = {
  technology: "Technology",
  programming: "Programming",
  concepts: "Concepts",
};

export default function App({ client = evidenceApi }: AppProps) {
  const [baseline, setBaseline] = useState<ResumeEvidenceRegistry | null>(null);
  const [draft, setDraft] = useState<ResumeEvidenceRegistry | null>(null);
  const [activeSection, setActiveSection] = useState<SectionKey>("user");
  const [selectedIds, setSelectedIds] = useState<SelectedIds>({});
  const [backendStatus, setBackendStatus] = useState<BackendStatus>("checking");
  const [isLoading, setIsLoading] = useState(true);
  const [isApplying, setIsApplying] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [applyError, setApplyError] = useState<string | null>(null);
  const [currentOperation, setCurrentOperation] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const resetEvidence = useCallback((evidence: ResumeEvidenceRegistry) => {
    const nextBaseline = cloneEvidence(evidence);
    setBaseline(nextBaseline);
    setDraft(cloneEvidence(evidence));
    setSelectedIds({
      projects: evidence.projects.projects[0]?.id,
      experience: evidence.experience.experience[0]?.id,
      education: evidence.education.education[0]?.id,
    });
    setApplyError(null);
    setCurrentOperation(null);
  }, []);

  const loadEvidence = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    setMessage(null);
    setBackendStatus("checking");

    try {
      const healthPromise = client
        .getHealth()
        .then(() => "online" as const)
        .catch(() => "offline" as const);
      const evidence = await client.getResumeEvidence();
      resetEvidence(evidence);
      setBackendStatus(await healthPromise);
    } catch (error) {
      setBackendStatus("offline");
      setLoadError(formatError(error));
    } finally {
      setIsLoading(false);
    }
  }, [client, resetEvidence]);

  useEffect(() => {
    void loadEvidence();
  }, [loadEvidence]);

  const dirty = useMemo(() => hasDraftChanges(baseline, draft), [baseline, draft]);
  const validationErrors = useMemo(() => (draft ? validateDraftEvidence(draft) : []), [draft]);
  const applyDisabled = !dirty || isApplying || validationErrors.length > 0;

  const mutateDraft = useCallback((mutator: (next: ResumeEvidenceRegistry) => void) => {
    setDraft((current) => {
      if (!current) {
        return current;
      }
      const next = cloneEvidence(current);
      mutator(next);
      return next;
    });
    setApplyError(null);
    setMessage(null);
  }, []);

  async function handleApply() {
    if (!baseline || !draft || applyDisabled) {
      return;
    }

    setIsApplying(true);
    setApplyError(null);
    setMessage(null);

    let operationLabel: string | null = null;
    try {
      const operationCount = await applyEvidenceChanges(client, baseline, draft, (operation) => {
        operationLabel = describeOperation(operation);
        setCurrentOperation(operationLabel);
      });
      const freshEvidence = await client.getResumeEvidence();
      resetEvidence(freshEvidence);
      setMessage(`${operationCount} operation${operationCount === 1 ? "" : "s"} applied.`);
    } catch (error) {
      const prefix = operationLabel ? `${operationLabel}: ` : "";
      setApplyError(`${prefix}${formatError(error)}`);
    } finally {
      setCurrentOperation(null);
      setIsApplying(false);
    }
  }

  function handleDiscard() {
    if (!baseline) {
      return;
    }
    setDraft(cloneEvidence(baseline));
    setSelectedIds({
      projects: baseline.projects.projects[0]?.id,
      experience: baseline.experience.experience[0]?.id,
      education: baseline.education.education[0]?.id,
    });
    setApplyError(null);
    setMessage("Draft discarded.");
  }

  function addProject() {
    const project = createBlankProject();
    mutateDraft((next) => {
      next.projects.projects.push(project);
    });
    setSelectedIds((current) => ({ ...current, projects: project.id }));
    setActiveSection("projects");
  }

  function updateProject(id: string, patch: Partial<ProjectRecord>) {
    mutateDraft((next) => {
      next.projects.projects = next.projects.projects.map((project) =>
        project.id === id ? { ...project, ...patch } : project,
      );
    });
  }

  function deleteProject(id: string) {
    let nextSelected: string | undefined;
    mutateDraft((next) => {
      next.projects.projects = next.projects.projects.filter((project) => project.id !== id);
      nextSelected = next.projects.projects[0]?.id;
    });
    setSelectedIds((current) => ({
      ...current,
      projects: current.projects === id ? nextSelected : current.projects,
    }));
  }

  function addExperience() {
    const experience = createBlankExperience();
    mutateDraft((next) => {
      next.experience.experience.push(experience);
    });
    setSelectedIds((current) => ({ ...current, experience: experience.id }));
    setActiveSection("experience");
  }

  function updateExperience(id: string, patch: Partial<ExperienceRecord>) {
    mutateDraft((next) => {
      next.experience.experience = next.experience.experience.map((experience) =>
        experience.id === id ? { ...experience, ...patch } : experience,
      );
    });
  }

  function deleteExperience(id: string) {
    let nextSelected: string | undefined;
    mutateDraft((next) => {
      next.experience.experience = next.experience.experience.filter(
        (experience) => experience.id !== id,
      );
      nextSelected = next.experience.experience[0]?.id;
    });
    setSelectedIds((current) => ({
      ...current,
      experience: current.experience === id ? nextSelected : current.experience,
    }));
  }

  function addEducation() {
    const education = createBlankEducation();
    mutateDraft((next) => {
      next.education.education.push(education);
    });
    setSelectedIds((current) => ({ ...current, education: education.id }));
    setActiveSection("education");
  }

  function updateEducation(id: string, patch: Partial<EducationRecord>) {
    mutateDraft((next) => {
      next.education.education = next.education.education.map((education) =>
        education.id === id ? { ...education, ...patch } : education,
      );
    });
  }

  function deleteEducation(id: string) {
    let nextSelected: string | undefined;
    mutateDraft((next) => {
      next.education.education = next.education.education.filter(
        (education) => education.id !== id,
      );
      nextSelected = next.education.education[0]?.id;
    });
    setSelectedIds((current) => ({
      ...current,
      education: current.education === id ? nextSelected : current.education,
    }));
  }

  const validationMessage = dirty && validationErrors.length > 0 ? validationErrors[0] : null;

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <span className="brand-mark">JF</span>
          <div>
            <h1>Resume Evidence</h1>
            <span className="subtle-text">JobForge Workbench</span>
          </div>
        </div>

        <div className="topbar-actions">
          <BackendStatusPill status={backendStatus} />
          {dirty ? <span className="dirty-pill">Unsaved</span> : <span className="clean-pill">Saved</span>}
          <button
            className="button secondary"
            type="button"
            onClick={() => void loadEvidence()}
            disabled={isLoading || isApplying}
            title="Reload evidence"
          >
            <RefreshCw aria-hidden="true" size={17} />
            Reload
          </button>
          <button
            className="button secondary"
            type="button"
            onClick={handleDiscard}
            disabled={!dirty || isApplying}
            title="Discard draft changes"
          >
            <RotateCcw aria-hidden="true" size={17} />
            Discard
          </button>
          <button
            className="button primary"
            type="button"
            onClick={() => void handleApply()}
            disabled={applyDisabled}
            title="Apply staged changes"
          >
            {isApplying ? (
              <Loader2 className="spin" aria-hidden="true" size={17} />
            ) : (
              <Save aria-hidden="true" size={17} />
            )}
            Apply
          </button>
        </div>
      </header>

      <div className="workspace">
        <nav className="section-nav" aria-label="Evidence sections">
          {sectionDefinitions.map((section) => (
            <NavButton
              key={section.key}
              active={activeSection === section.key}
              count={draft ? sectionCount(section.key, draft) : undefined}
              icon={section.icon}
              label={section.label}
              onClick={() => setActiveSection(section.key)}
            />
          ))}
        </nav>

        <section className="content-area">
          {isLoading ? (
            <StatePanel icon={Loader2} spin title="Loading evidence" />
          ) : loadError || !draft ? (
            <StatePanel
              icon={AlertCircle}
              tone="error"
              title="Evidence unavailable"
              detail={loadError ?? "No evidence was returned."}
            >
              <button className="button secondary" type="button" onClick={() => void loadEvidence()}>
                <RefreshCw aria-hidden="true" size={17} />
                Reload
              </button>
            </StatePanel>
          ) : (
            <>
              <StatusMessages
                applyError={applyError}
                currentOperation={currentOperation}
                message={message}
                validationMessage={validationMessage}
              />
              {activeSection === "user" ? (
                <UserEditor
                  user={draft.user}
                  onChange={(patch) => {
                    mutateDraft((next) => {
                      next.user = { ...next.user, ...patch };
                    });
                  }}
                />
              ) : null}
              {activeSection === "skills" ? (
                <SkillsEditor
                  skills={draft.skills.skills}
                  onChange={(skills) => {
                    mutateDraft((next) => {
                      next.skills.skills = skills;
                    });
                  }}
                />
              ) : null}
              {activeSection === "projects" ? (
                <CollectionPanel
                  addLabel="Add Project"
                  getMeta={(project) =>
                    `${project.active ? "Active" : "Inactive"} | ${countSkills(project.skills)} skills`
                  }
                  getSearchText={(project) => `${project.name} ${project.summary}`}
                  records={draft.projects.projects}
                  selectedId={selectedIds.projects}
                  title="Projects"
                  onAdd={addProject}
                  onDelete={deleteProject}
                  onSelect={(id) => setSelectedIds((current) => ({ ...current, projects: id }))}
                  renderEditor={(project) => (
                    <ProjectRecordEditor
                      key={project.id}
                      project={project}
                      onChange={(patch) => updateProject(project.id, patch)}
                    />
                  )}
                />
              ) : null}
              {activeSection === "experience" ? (
                <CollectionPanel
                  addLabel="Add Experience"
                  getMeta={(experience) =>
                    `${experience.role || "Role"} | ${experience.start || "Start"}${
                      experience.end ? ` to ${experience.end}` : ""
                    }`
                  }
                  getSearchText={(experience) =>
                    `${experience.name} ${experience.role} ${experience.summary}`
                  }
                  records={draft.experience.experience}
                  selectedId={selectedIds.experience}
                  title="Experience"
                  onAdd={addExperience}
                  onDelete={deleteExperience}
                  onSelect={(id) => setSelectedIds((current) => ({ ...current, experience: id }))}
                  renderEditor={(experience) => (
                    <ExperienceRecordEditor
                      key={experience.id}
                      experience={experience}
                      onChange={(patch) => updateExperience(experience.id, patch)}
                    />
                  )}
                />
              ) : null}
              {activeSection === "education" ? (
                <CollectionPanel
                  addLabel="Add Education"
                  getMeta={(education) => `${education.degree || "Degree"} | ${education.location || "Location"}`}
                  getSearchText={(education) => `${education.name} ${education.degree} ${education.location}`}
                  records={draft.education.education}
                  selectedId={selectedIds.education}
                  title="Education"
                  onAdd={addEducation}
                  onDelete={deleteEducation}
                  onSelect={(id) => setSelectedIds((current) => ({ ...current, education: id }))}
                  renderEditor={(education) => (
                    <EducationRecordEditor
                      key={education.id}
                      education={education}
                      onChange={(patch) => updateEducation(education.id, patch)}
                    />
                  )}
                />
              ) : null}
            </>
          )}
        </section>
      </div>
    </main>
  );
}

function BackendStatusPill({ status }: { status: BackendStatus }) {
  const label =
    status === "checking"
      ? "Checking backend"
      : status === "online"
        ? "Backend online"
        : "Backend offline";
  return (
    <span className={`status-pill ${status}`}>
      <span className="status-dot" aria-hidden="true" />
      {label}
    </span>
  );
}

function NavButton({
  active,
  count,
  icon: Icon,
  label,
  onClick,
}: {
  active: boolean;
  count?: number;
  icon: LucideIcon;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      aria-current={active ? "page" : undefined}
      className={`nav-button ${active ? "active" : ""}`}
      type="button"
      onClick={onClick}
    >
      <Icon aria-hidden="true" size={18} />
      <span>{label}</span>
      {typeof count === "number" ? <span className="nav-count">{count}</span> : null}
    </button>
  );
}

function StatusMessages({
  applyError,
  currentOperation,
  message,
  validationMessage,
}: {
  applyError: string | null;
  currentOperation: string | null;
  message: string | null;
  validationMessage: string | null;
}) {
  if (!applyError && !currentOperation && !message && !validationMessage) {
    return null;
  }

  if (applyError) {
    return (
      <div className="notice error" role="alert">
        <AlertCircle aria-hidden="true" size={18} />
        {applyError}
      </div>
    );
  }

  if (validationMessage) {
    return (
      <div className="notice warning" role="status">
        <AlertCircle aria-hidden="true" size={18} />
        {validationMessage}
      </div>
    );
  }

  if (currentOperation) {
    return (
      <div className="notice pending" role="status">
        <Loader2 className="spin" aria-hidden="true" size={18} />
        {currentOperation}
      </div>
    );
  }

  return (
    <div className="notice success" role="status">
      <CheckCircle2 aria-hidden="true" size={18} />
      {message}
    </div>
  );
}

function UserEditor({
  user,
  onChange,
}: {
  user: ResumeEvidenceRegistry["user"];
  onChange: (patch: Partial<ResumeEvidenceRegistry["user"]>) => void;
}) {
  return (
    <div className="editor-surface">
      <SectionHeader title="User" eyebrow="Contact" />
      <div className="field-grid">
        <TextField label="Name" value={user.name} onChange={(name) => onChange({ name })} />
        <TextField label="Email" value={user.email} onChange={(email) => onChange({ email })} />
        <TextField label="Phone" value={user.phone} onChange={(phone) => onChange({ phone })} />
        <TextField
          label="LinkedIn"
          value={user.linkedin ?? ""}
          onChange={(linkedin) => onChange({ linkedin: optionalText(linkedin) })}
        />
        <TextField
          label="GitHub"
          value={user.github ?? ""}
          onChange={(github) => onChange({ github: optionalText(github) })}
        />
        <TextField
          label="Website"
          value={user.website ?? ""}
          onChange={(website) => onChange({ website: optionalText(website) })}
        />
      </div>
    </div>
  );
}

function SkillsEditor({
  skills,
  onChange,
}: {
  skills: ProjectSkills;
  onChange: (skills: ProjectSkills) => void;
}) {
  return (
    <div className="editor-surface">
      <SectionHeader title="Skills" eyebrow="Inventory" />
      <SkillBucketsEditor skills={skills} onChange={onChange} />
    </div>
  );
}

function CollectionPanel<T extends CollectionRecord>({
  addLabel,
  getMeta,
  getSearchText,
  records,
  renderEditor,
  selectedId,
  title,
  onAdd,
  onDelete,
  onSelect,
}: {
  addLabel: string;
  getMeta: (record: T) => string;
  getSearchText: (record: T) => string;
  records: T[];
  renderEditor: (record: T) => ReactNode;
  selectedId?: string;
  title: string;
  onAdd: () => void;
  onDelete: (id: string) => void;
  onSelect: (id: string) => void;
}) {
  const [query, setQuery] = useState("");
  const normalizedQuery = query.trim().toLowerCase();
  const selectedRecord = records.find((record) => record.id === selectedId) ?? records[0];
  const filteredRecords = normalizedQuery
    ? records.filter((record) => getSearchText(record).toLowerCase().includes(normalizedQuery))
    : records;

  return (
    <div className="collection-layout">
      <aside className="record-list-pane">
        <div className="collection-toolbar">
          <SectionHeader title={title} eyebrow={`${records.length} entries`} compact />
          <button className="button primary compact" type="button" onClick={onAdd}>
            <Plus aria-hidden="true" size={16} />
            {addLabel}
          </button>
        </div>
        <label className="search-box">
          <Search aria-hidden="true" size={17} />
          <input
            aria-label={`Search ${title}`}
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
        <div className="record-list">
          {filteredRecords.length === 0 ? (
            <p className="empty-note">No matches.</p>
          ) : (
            filteredRecords.map((record) => (
              <div
                className={`record-row ${record.id === selectedRecord?.id ? "selected" : ""}`}
                key={record.id}
              >
                <button className="record-select" type="button" onClick={() => onSelect(record.id)}>
                  <span className="record-title">{record.name || "Untitled"}</span>
                  <span className="record-meta">{getMeta(record)}</span>
                  {isTempId(record.id) ? <span className="record-temp">New</span> : null}
                </button>
                <button
                  aria-label={`Delete ${record.name || "record"}`}
                  className="icon-button danger"
                  title={`Delete ${record.name || "record"}`}
                  type="button"
                  onClick={() => onDelete(record.id)}
                >
                  <Trash2 aria-hidden="true" size={16} />
                </button>
              </div>
            ))
          )}
        </div>
      </aside>
      <section className="record-editor">
        {selectedRecord ? renderEditor(selectedRecord) : <StatePanel icon={AlertCircle} title="No records" />}
      </section>
    </div>
  );
}

function ProjectRecordEditor({
  project,
  onChange,
}: {
  project: ProjectRecord;
  onChange: (patch: Partial<ProjectRecord>) => void;
}) {
  return (
    <div className="editor-surface">
      <SectionHeader title={project.name || "Untitled Project"} eyebrow={project.id} />
      <div className="field-grid">
        <TextField label="Name" value={project.name} onChange={(name) => onChange({ name })} />
        <ToggleField
          checked={project.active}
          label="Active"
          onChange={(active) => onChange({ active })}
        />
      </div>
      <TextareaField
        label="Summary"
        value={project.summary}
        onChange={(summary) => onChange({ summary })}
      />
      <TextListEditor
        label="Highlights"
        minItems={1}
        values={project.highlights}
        onChange={(highlights) => onChange({ highlights })}
      />
      <SkillBucketsEditor
        skills={project.skills}
        onChange={(skills) => onChange({ skills })}
      />
      <TextListEditor
        label="Links"
        values={project.links ?? []}
        onChange={(links) => onChange({ links: optionalList(links) })}
      />
    </div>
  );
}

function ExperienceRecordEditor({
  experience,
  onChange,
}: {
  experience: ExperienceRecord;
  onChange: (patch: Partial<ExperienceRecord>) => void;
}) {
  return (
    <div className="editor-surface">
      <SectionHeader title={experience.name || "Untitled Experience"} eyebrow={experience.id} />
      <div className="field-grid">
        <TextField
          label="Organization"
          value={experience.name}
          onChange={(name) => onChange({ name })}
        />
        <TextField label="Role" value={experience.role} onChange={(role) => onChange({ role })} />
        <TextField
          label="Location"
          value={experience.location}
          onChange={(location) => onChange({ location })}
        />
        <TextField label="Start" value={experience.start} onChange={(start) => onChange({ start })} />
        <TextField
          label="End"
          value={experience.end ?? ""}
          onChange={(end) => onChange({ end: optionalText(end) })}
        />
        <ToggleField
          checked={experience.active}
          label="Active"
          onChange={(active) => onChange({ active })}
        />
      </div>
      <TextareaField
        label="Summary"
        value={experience.summary}
        onChange={(summary) => onChange({ summary })}
      />
      <TextListEditor
        label="Highlights"
        minItems={1}
        values={experience.highlights}
        onChange={(highlights) => onChange({ highlights })}
      />
      <SkillBucketsEditor
        skills={experience.skills}
        onChange={(skills) => onChange({ skills })}
      />
      <TextListEditor
        label="Links"
        values={experience.links ?? []}
        onChange={(links) => onChange({ links: optionalList(links) })}
      />
    </div>
  );
}

function EducationRecordEditor({
  education,
  onChange,
}: {
  education: EducationRecord;
  onChange: (patch: Partial<EducationRecord>) => void;
}) {
  return (
    <div className="editor-surface">
      <SectionHeader title={education.name || "Untitled Education"} eyebrow={education.id} />
      <div className="field-grid">
        <TextField label="Name" value={education.name} onChange={(name) => onChange({ name })} />
        <TextField
          label="Degree"
          value={education.degree}
          onChange={(degree) => onChange({ degree })}
        />
        <TextField label="Grade" value={education.grade} onChange={(grade) => onChange({ grade })} />
        <TextField
          label="Location"
          value={education.location}
          onChange={(location) => onChange({ location })}
        />
        <TextField label="Start" value={education.start} onChange={(start) => onChange({ start })} />
        <TextField
          label="End"
          value={education.end ?? ""}
          onChange={(end) => onChange({ end: optionalText(end) })}
        />
      </div>
      <TextListEditor
        label="Relevant Coursework"
        values={education.relevant_coursework}
        onChange={(relevant_coursework) => onChange({ relevant_coursework })}
      />
    </div>
  );
}

function SkillBucketsEditor({
  skills,
  onChange,
}: {
  skills: ProjectSkills;
  onChange: (skills: ProjectSkills) => void;
}) {
  return (
    <div className="bucket-grid">
      {skillCategories.map((category) => (
        <TextListEditor
          key={category}
          label={categoryLabels[category]}
          values={skills[category]}
          onChange={(values) => onChange({ ...skills, [category]: values })}
        />
      ))}
    </div>
  );
}

function TextField({
  label,
  onChange,
  value,
}: {
  label: string;
  onChange: (value: string) => void;
  value: string;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <input value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function TextareaField({
  label,
  onChange,
  value,
}: {
  label: string;
  onChange: (value: string) => void;
  value: string;
}) {
  return (
    <label className="field full">
      <span>{label}</span>
      <textarea value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function ToggleField({
  checked,
  label,
  onChange,
}: {
  checked: boolean;
  label: string;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className="toggle-field">
      <input
        checked={checked}
        type="checkbox"
        onChange={(event) => onChange(event.target.checked)}
      />
      <span>{label}</span>
    </label>
  );
}

function TextListEditor({
  label,
  minItems = 0,
  onChange,
  values,
}: {
  label: string;
  minItems?: number;
  onChange: (values: string[]) => void;
  values: string[];
}) {
  function updateValue(index: number, value: string) {
    const next = [...values];
    next[index] = value;
    onChange(next);
  }

  function removeValue(index: number) {
    if (values.length <= minItems) {
      return;
    }
    onChange(values.filter((_, currentIndex) => currentIndex !== index));
  }

  return (
    <div className="list-editor">
      <div className="list-editor-header">
        <span>{label}</span>
        <button
          aria-label={`Add ${label}`}
          className="icon-button"
          title={`Add ${label}`}
          type="button"
          onClick={() => onChange([...values, ""])}
        >
          <Plus aria-hidden="true" size={16} />
        </button>
      </div>
      {values.length === 0 ? <p className="empty-note">None.</p> : null}
      {values.map((value, index) => (
        <div className="list-row" key={index}>
          <input
            aria-label={`${label} ${index + 1}`}
            value={value}
            onChange={(event) => updateValue(index, event.target.value)}
          />
          <button
            aria-label={`Remove ${label} ${index + 1}`}
            className="icon-button danger"
            disabled={values.length <= minItems}
            title={`Remove ${label} ${index + 1}`}
            type="button"
            onClick={() => removeValue(index)}
          >
            <Trash2 aria-hidden="true" size={16} />
          </button>
        </div>
      ))}
    </div>
  );
}

function SectionHeader({
  compact = false,
  eyebrow,
  title,
}: {
  compact?: boolean;
  eyebrow: string;
  title: string;
}) {
  return (
    <div className={`section-header ${compact ? "compact" : ""}`}>
      <span>{eyebrow}</span>
      <h2>{title}</h2>
    </div>
  );
}

function StatePanel({
  children,
  detail,
  icon: Icon,
  spin = false,
  title,
  tone,
}: {
  children?: ReactNode;
  detail?: string;
  icon: LucideIcon;
  spin?: boolean;
  title: string;
  tone?: "error";
}) {
  return (
    <div className={`state-panel ${tone ?? ""}`}>
      <Icon className={spin ? "spin" : ""} aria-hidden="true" size={28} />
      <h2>{title}</h2>
      {detail ? <p>{detail}</p> : null}
      {children}
    </div>
  );
}

function sectionCount(section: SectionKey, evidence: ResumeEvidenceRegistry): number | undefined {
  if (section === "projects") {
    return evidence.projects.projects.length;
  }
  if (section === "experience") {
    return evidence.experience.experience.length;
  }
  if (section === "education") {
    return evidence.education.education.length;
  }
  return undefined;
}

function countSkills(skills: ProjectSkills): number {
  return skills.technology.length + skills.programming.length + skills.concepts.length;
}

function optionalText(value: string): string | null {
  return value.length > 0 ? value : null;
}

function optionalList(values: string[]): string[] | null {
  return values.length > 0 ? values : null;
}

function formatError(error: unknown): string {
  if (error instanceof ApiError) {
    return error.detail;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Unknown error.";
}
