from __future__ import annotations
import shlex
from typing import Callable, TextIO

from app.resume_evidence.base_cli import EvidenceCLIBase
from app.resume_evidence.selection_ui import ChoiceFunc, PickerFunc, choose_index, choose_value
from app.resume_evidence.session import ProjectsEvidenceSession, PendingProjectChanges

class ProjectsEvidenceCLI(EvidenceCLIBase):
    prompt_label = "projects"
    action_choices: list[tuple[str | None, str]] = [
        ("edit", "edit"),
        ("create", "create"),
        ("delete", "delete"),
        ("quit", "quit"),
    ]

    def __init__(
        self,
        session: ProjectsEvidenceSession,
        *,
        input_func: Callable[[str], str] = input,
        output: TextIO | None = None,
        picker: PickerFunc | None = None,
        action_picker: ChoiceFunc[str] | None = None,
    ):
        super().__init__(input_func=input_func, output=output)
        self.session = session
        self.picker = picker or choose_index
        self.action_picker = action_picker or choose_value

    def run(self) -> int:
        self._println(f"{self.prompt_label.capitalize()} evidence CLI. Type 'help' for commands.")

        while True:
            self._list_projects()
            action = self.action_picker("Choose project action", self.action_choices)
            if action is not None:
                if not self._execute_raw_command(action):
                    return 0
                continue

            if not self._run_typed_command_once():
                return 0

    def _run_typed_command_once(self) -> bool:
        try:
            raw_command = self.input_func(f"{self.prompt_label}> ").strip()
        except EOFError:
            return self._handle_quit()
        except KeyboardInterrupt:
            self._println("\nInterrupted. Type 'quit' to exit.")
            return True

        if not raw_command:
            return True

        return self._execute_raw_command(raw_command)

    def _execute_raw_command(self, raw_command: str) -> bool:
        try:
            return self.execute(raw_command)
        except ValueError as exc:
            self._println(f"Error: {exc}")
            return True
        except IndexError as exc:
            self._println(f"Error: {exc}")
            return True

    def execute(self, raw_command: str) -> bool:
        parts = shlex.split(raw_command)
        command = parts[0].lower()

        if command == "help":
            self._show_help()
            return True
        if command == "list":
            self._list_projects()
            return True
        if command == "show":
            index = self._resolve_project_index_or_pick(parts, "show")
            if index is not None:
                self._show_project(index)
            return True
        if command == "create":
            self._create_project()
            return True
        if command == "edit":
            index = self._resolve_project_index_or_pick(parts, "edit")
            if index is not None:
                self._edit_project(index)
            return True
        if command == "delete":
            index = self._resolve_project_index_or_pick(parts, "delete")
            if index is not None:
                self._delete_project(index)
            return True
        if command == "apply":
            self._apply_changes()
            return True
        if command == "reload":
            self._reload()
            return True
        if command == "quit":
            return self._handle_quit()

        raise ValueError(f"Unknown command '{command}'")

    def _show_help(self) -> None:
        self._println("Commands:")
        self._println("  help           Show available commands")
        self._println("  list           List staged projects")
        self._println("  show [index]   Show a staged project")
        self._println("  create         Create a new staged project")
        self._println("  edit [index]   Edit an existing staged project")
        self._println("  delete [index] Delete a staged project")
        self._println("  apply          Save staged changes to disk")
        self._println("  reload         Discard staged changes and reload from disk")
        self._println("  quit           Exit the CLI")

    def _list_projects(self) -> None:
        projects = self.session.list_projects()
        if not projects:
            self._println("No projects in staged state.")
            return

        for index, project in enumerate(projects, start=1):
            status = "active" if project.active else "inactive"
            self._println(f"{index}. {project.name} [{status}]")

        if self.session.dirty:
            self._println("Staged changes are pending. Run 'apply' to write them to disk.")

    def _show_project(self, index: int) -> None:
        project = self.session.get_project(index)
        self._println(f"{index}. {project.name}")
        self._println(f"Summary: {project.summary}")
        self._println(f"Active: {'yes' if project.active else 'no'}")
        self._show_list("Highlights", project.highlights)
        self._show_list("Technology", project.skills.technology)
        self._show_list("Programming", project.skills.programming)
        self._show_list("Concepts", project.skills.concepts)
        self._show_list("Links", project.links or [])

    def _create_project(self) -> None:
        project = self.session.create_project(
            name=self._prompt_required_text("Name"),
            summary=self._prompt_required_text("Summary"),
            highlights=self._prompt_list("Highlights", required=True),
            active=self._prompt_bool("Active", default=True),
            technology=self._prompt_comma_list("Technology skills"),
            programming=self._prompt_comma_list("Programming skills"),
            concepts=self._prompt_comma_list("Concepts"),
            links=self._prompt_optional_list("Links"),
        )
        self._println(f"Staged new project '{project.name}'. Run 'apply' to save.")

    def _edit_project(self, index: int) -> None:
        project = self.session.get_project(index)
        updated = self.session.update_project(
            index,
            name=self._prompt_required_text("Name", default=project.name),
            summary=self._prompt_required_text("Summary", default=project.summary),
            highlights=self._prompt_editable_highlights(project.highlights),
            active=self._prompt_bool("Active", default=project.active),
            technology=self._prompt_comma_list(
                "Technology skills",
                default_items=project.skills.technology,
            ),
            programming=self._prompt_comma_list(
                "Programming skills",
                default_items=project.skills.programming,
            ),
            concepts=self._prompt_comma_list(
                "Concepts",
                default_items=project.skills.concepts,
            ),
            links=self._prompt_optional_editable_list("Links", project.links),
        )
        self._println(f"Staged updates for '{updated.name}'. Run 'apply' to save.")

    def _prompt_editable_highlights(self, current_highlights: list[str]) -> list[str]:
        self._show_indexed_list("Current Highlights", current_highlights)
        if self._confirm("Keep current highlights?", default=True):
            return list(current_highlights)
        return self._run_highlights_editor(current_highlights)

    def _run_highlights_editor(self, current_highlights: list[str]) -> list[str]:
        highlights = list(current_highlights)
        self._println("Editing highlights. Type 'help' for commands.")
        self._show_indexed_list("Highlights", highlights)

        while True:
            try:
                raw_command = self.input_func("highlights> ").strip()
            except EOFError:
                return highlights
            except KeyboardInterrupt:
                self._println("\nInterrupted. Type 'done' to finish editing highlights.")
                continue

            if not raw_command:
                continue

            try:
                parts = shlex.split(raw_command)
                command = parts[0].lower()

                if command == "help":
                    self._show_highlights_help()
                elif command == "list":
                    self._show_indexed_list("Highlights", highlights)
                elif command == "edit":
                    highlight_index = self._resolve_highlight_index_or_pick(
                        parts,
                        "edit",
                        highlights,
                    )
                    if highlight_index is not None:
                        highlights[highlight_index] = self._prompt_required_text(
                            "Highlight",
                            default=highlights[highlight_index],
                        )
                elif command == "add":
                    if len(parts) != 1:
                        raise ValueError("Usage: add")
                    highlights.append(self._prompt_required_text("Highlight"))
                elif command == "delete":
                    highlight_index = self._resolve_highlight_index_or_pick(
                        parts,
                        "delete",
                        highlights,
                    )
                    if highlight_index is not None:
                        if len(highlights) == 1:
                            raise ValueError("At least one highlight is required.")
                        deleted = highlights.pop(highlight_index)
                        self._println(f"Deleted highlight: {deleted}")
                elif command == "done":
                    if len(parts) != 1:
                        raise ValueError("Usage: done")
                    return highlights
                else:
                    raise ValueError(f"Unknown highlights command '{command}'")
            except ValueError as exc:
                self._println(f"Error: {exc}")

    def _show_highlights_help(self) -> None:
        self._println("Highlight commands:")
        self._println("  help           Show highlight commands")
        self._println("  list           List staged highlights")
        self._println("  edit [index]   Edit a highlight")
        self._println("  add            Append a new highlight")
        self._println("  delete [index] Delete a highlight")
        self._println("  done           Finish editing highlights")

    def _show_indexed_list(self, label: str, items: list[str]) -> None:
        if not items:
            self._println(f"{label}: none")
            return
        self._println(f"{label}:")
        for index, item in enumerate(items, start=1):
            self._println(f"  {index}. {item}")

    def _parse_highlight_index(self, parts: list[str], command: str, highlights: list[str]) -> int:
        if len(parts) != 2:
            raise ValueError(f"Usage: {command} <index>")
        try:
            index = int(parts[1])
        except ValueError as exc:
            raise ValueError(f"Highlight index must be an integer for '{command}'") from exc
        if index < 1 or index > len(highlights):
            raise ValueError(f"Highlight index {index} is out of range")
        return index - 1

    def _resolve_highlight_index_or_pick(
        self,
        parts: list[str],
        command: str,
        highlights: list[str],
    ) -> int | None:
        if len(parts) == 2:
            return self._parse_highlight_index(parts, command, highlights)
        if len(parts) != 1:
            raise ValueError(f"Usage: {command} [index]")

        labels = [f"{index}. {highlight}" for index, highlight in enumerate(highlights, start=1)]
        selected = self.picker(f"Choose a highlight to {command}", labels)
        if selected is None:
            self._println(f"No highlight selected. Use '{command} <index>' to choose directly.")
            return None
        if selected < 1 or selected > len(highlights):
            raise ValueError(f"Highlight index {selected} is out of range")
        return selected - 1

    def _delete_project(self, index: int) -> None:
        project = self.session.get_project(index)
        if not self._confirm(
            f"Delete '{project.name}' from staged state?",
            default=False,
        ):
            self._println("Delete canceled.")
            return

        deleted = self.session.delete_project(index)
        self._println(f"Staged deletion for '{deleted.name}'. Run 'apply' to save.")

    def _apply_changes(self) -> None:
        changes = self.session.pending_changes()
        if changes.is_empty():
            self._println("No staged changes to apply.")
            return

        self._print_pending_changes(changes)
        if not self._confirm("Write staged changes to disk?", default=False):
            self._println("Apply canceled.")
            return

        self.session.apply()
        self._println(f"Saved staged changes to {self.session.path}")

    def _reload(self) -> None:
        if self.session.dirty and not self._confirm(
            "Discard staged changes and reload from disk?",
            default=False,
        ):
            self._println("Reload canceled.")
            return

        self.session.reload()
        self._println("Reloaded projects evidence from disk.")

    def _handle_quit(self) -> bool:
        if self.session.dirty and not self._confirm(
            "Discard unapplied changes and quit?",
            default=False,
        ):
            self._println("Quit canceled.")
            return True

        self._println("Goodbye.")
        return False

    def _parse_single_index(self, parts: list[str], command: str) -> int:
        if len(parts) != 2:
            raise ValueError(f"Usage: {command} <index>")
        try:
            return int(parts[1])
        except ValueError as exc:
            raise ValueError(f"Project index must be an integer for '{command}'") from exc

    def _resolve_project_index_or_pick(self, parts: list[str], command: str) -> int | None:
        if len(parts) == 2:
            return self._parse_single_index(parts, command)
        if len(parts) != 1:
            raise ValueError(f"Usage: {command} [index]")

        projects = self.session.list_projects()
        if not projects:
            self._println("No projects in staged state.")
            return None

        labels = []
        for index, project in enumerate(projects, start=1):
            status = "active" if project.active else "inactive"
            labels.append(f"{index}. {project.name} [{status}]")

        selected = self.picker(f"Choose a project to {command}", labels)
        if selected is None:
            self._println(f"No project selected. Use '{command} <index>' to choose directly.")
            return None
        if selected < 1 or selected > len(projects):
            raise IndexError(f"Project index {selected} is out of range")
        return selected

    def _print_pending_changes(self, changes: PendingProjectChanges) -> None:
        self._println(
            "Pending changes: "
            f"{len(changes.created)} created, "
            f"{len(changes.updated)} updated, "
            f"{len(changes.deleted)} deleted."
        )
        if changes.created:
            self._println(f"Created: {', '.join(changes.created)}")
        if changes.updated:
            self._println(f"Updated: {', '.join(changes.updated)}")
        if changes.deleted:
            self._println(f"Deleted: {', '.join(changes.deleted)}")
