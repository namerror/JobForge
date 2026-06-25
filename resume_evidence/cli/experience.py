from __future__ import annotations

import shlex
from typing import Callable, TextIO

from resume_evidence.cli.base import EvidenceCLIBase
from resume_evidence.cli.selection_ui import ChoiceFunc, PickerFunc, choose_index, choose_value
from resume_evidence.session import ExperienceEvidenceSession, PendingExperienceChanges


class ExperienceEvidenceCLI(EvidenceCLIBase):
    prompt_label = "experience"
    action_choices: list[tuple[str | None, str]] = [
        ("list", "list"),
        ("show", "show"),
        ("edit", "edit"),
        ("create", "create"),
        ("delete", "delete"),
        ("apply", "apply"),
        ("reload", "reload"),
        ("quit", "quit"),
    ]

    def __init__(
        self,
        session: ExperienceEvidenceSession,
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
            self._list_experience()
            action = self.action_picker("Choose experience action", self.action_choices)
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
            self._list_experience()
            return True
        if command == "show":
            index = self._resolve_experience_index_or_pick(parts, "show")
            if index is not None:
                self._show_experience(index)
            return True
        if command == "create":
            self._create_experience()
            return True
        if command == "edit":
            index = self._resolve_experience_index_or_pick(parts, "edit")
            if index is not None:
                self._edit_experience(index)
            return True
        if command == "delete":
            index = self._resolve_experience_index_or_pick(parts, "delete")
            if index is not None:
                self._delete_experience(index)
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
        self._println("  list           List staged experience entries")
        self._println("  show [index]   Show a staged experience entry")
        self._println("  create         Create a new staged experience entry")
        self._println("  edit [index]   Edit an existing staged experience entry")
        self._println("  delete [index] Delete a staged experience entry")
        self._println("  apply          Save staged changes to disk")
        self._println("  reload         Discard staged changes and reload from disk")
        self._println("  quit           Exit the CLI")

    def _list_experience(self) -> None:
        experience = self.session.list_experience()
        if not experience:
            self._println("No experience entries in staged state.")
            return

        for index, item in enumerate(experience, start=1):
            status = "active" if item.active else "inactive"
            self._println(f"{index}. {item.name} [{status}]")

        if self.session.dirty:
            self._println("Staged changes are pending. Run 'apply' to write them to disk.")

    def _show_experience(self, index: int) -> None:
        item = self.session.get_experience(index)
        self._println(f"{index}. {item.name}")
        self._println(f"Role: {item.role}")
        self._println(f"Summary: {item.summary}")
        self._println(f"Active: {'yes' if item.active else 'no'}")
        self._println(f"Location: {item.location}")
        self._println(f"Start: {item.start}")
        self._show_optional_text("End", item.end)
        self._show_list("Highlights", item.highlights)
        self._show_list("Technology", item.skills.technology)
        self._show_list("Programming", item.skills.programming)
        self._show_list("Concepts", item.skills.concepts)
        self._show_list("Links", item.links or [])

    def _create_experience(self) -> None:
        item = self.session.create_experience(
            name=self._prompt_required_text("Name"),
            role=self._prompt_required_text("Role"),
            summary=self._prompt_required_text("Summary"),
            highlights=self._prompt_list("Highlights", required=True),
            active=self._prompt_bool("Active", default=True),
            technology=self._prompt_comma_list("Technology skills"),
            programming=self._prompt_comma_list("Programming skills"),
            concepts=self._prompt_comma_list("Concepts"),
            location=self._prompt_required_text("Location"),
            start=self._prompt_required_text("Start"),
            end=self._prompt_optional_text("End"),
            links=self._prompt_optional_list("Links"),
        )
        self._println(f"Staged new experience entry '{item.name}'. Run 'apply' to save.")

    def _edit_experience(self, index: int) -> None:
        item = self.session.get_experience(index)
        updated = self.session.update_experience(
            index,
            name=self._prompt_required_text("Name", default=item.name),
            role=self._prompt_required_text("Role", default=item.role),
            summary=self._prompt_required_text("Summary", default=item.summary),
            highlights=self._prompt_editable_highlights(item.highlights),
            active=self._prompt_bool("Active", default=item.active),
            technology=self._prompt_comma_list(
                "Technology skills",
                default_items=item.skills.technology,
            ),
            programming=self._prompt_comma_list(
                "Programming skills",
                default_items=item.skills.programming,
            ),
            concepts=self._prompt_comma_list("Concepts", default_items=item.skills.concepts),
            location=self._prompt_required_text("Location", default=item.location),
            start=self._prompt_required_text("Start", default=item.start),
            end=self._prompt_optional_editable_text("End", item.end),
            links=self._prompt_optional_editable_list("Links", item.links),
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

    def _parse_highlight_index(
        self,
        parts: list[str],
        command: str,
        highlights: list[str],
    ) -> int:
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

        labels = [
            f"{index}. {highlight}" for index, highlight in enumerate(highlights, start=1)
        ]
        selected = self.picker(f"Choose a highlight to {command}", labels)
        if selected is None:
            self._println(f"No highlight selected. Use '{command} <index>' to choose directly.")
            return None
        if selected < 1 or selected > len(highlights):
            raise ValueError(f"Highlight index {selected} is out of range")
        return selected - 1

    def _delete_experience(self, index: int) -> None:
        item = self.session.get_experience(index)
        if not self._confirm(
            f"Delete '{item.name}' from staged state?",
            default=False,
        ):
            self._println("Delete canceled.")
            return

        deleted = self.session.delete_experience(index)
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
        self._println("Reloaded experience evidence from disk.")

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
        return super()._parse_single_index(parts, command, "Experience")

    def _resolve_experience_index_or_pick(self, parts: list[str], command: str) -> int | None:
        if len(parts) == 2:
            return self._parse_single_index(parts, command)
        if len(parts) != 1:
            raise ValueError(f"Usage: {command} [index]")

        experience = self.session.list_experience()
        if not experience:
            self._println("No experience entries in staged state.")
            return None

        labels = []
        for index, item in enumerate(experience, start=1):
            status = "active" if item.active else "inactive"
            labels.append(f"{index}. {item.name} [{status}]")

        selected = self.picker(f"Choose an experience entry to {command}", labels)
        if selected is None:
            self._println(
                f"No experience entry selected. Use '{command} <index>' to choose directly."
            )
            return None
        if selected < 1 or selected > len(experience):
            raise IndexError(f"Experience index {selected} is out of range")
        return selected

    def _print_pending_changes(self, changes: PendingExperienceChanges) -> None:
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
