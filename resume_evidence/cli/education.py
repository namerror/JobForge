from __future__ import annotations

import shlex
from typing import Callable, TextIO

from resume_evidence.cli.base import EvidenceCLIBase
from resume_evidence.session import EducationEvidenceSession, PendingEducationChanges


class EducationEvidenceCLI(EvidenceCLIBase):
    prompt_label = "education"

    def __init__(
        self,
        session: EducationEvidenceSession,
        *,
        input_func: Callable[[str], str] = input,
        output: TextIO | None = None,
    ):
        super().__init__(input_func=input_func, output=output)
        self.session = session

    def execute(self, raw_command: str) -> bool:
        parts = shlex.split(raw_command)
        command = parts[0].lower()

        if command == "help":
            self._show_help()
            return True
        if command == "list":
            self._list_education()
            return True
        if command == "show":
            self._show_education(self._parse_single_index(parts, "show"))
            return True
        if command == "create":
            self._create_education()
            return True
        if command == "edit":
            self._edit_education(self._parse_single_index(parts, "edit"))
            return True
        if command == "delete":
            self._delete_education(self._parse_single_index(parts, "delete"))
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
        self._println("  list           List staged education entries")
        self._println("  show <index>   Show a staged education entry")
        self._println("  create         Create a new staged education entry")
        self._println("  edit <index>   Edit an existing staged education entry")
        self._println("  delete <index> Delete a staged education entry")
        self._println("  apply          Save staged changes to disk")
        self._println("  reload         Discard staged changes and reload from disk")
        self._println("  quit           Exit the CLI")

    def _list_education(self) -> None:
        education = self.session.list_education()
        if not education:
            self._println("No education entries in staged state.")
            return

        for index, item in enumerate(education, start=1):
            self._println(f"{index}. {item.name} - {item.degree}")

        if self.session.dirty:
            self._println("Staged changes are pending. Run 'apply' to write them to disk.")

    def _show_education(self, index: int) -> None:
        item = self.session.get_education(index)
        self._println(f"{index}. {item.name}")
        self._println(f"Degree: {item.degree}")
        self._println(f"Grade: {item.grade}")
        self._println(f"Start: {item.start}")
        self._show_optional_text("End", item.end)
        self._println(f"Location: {item.location}")
        self._show_list("Relevant coursework", item.relevant_coursework)

    def _create_education(self) -> None:
        item = self.session.create_education(
            name=self._prompt_required_text("Name"),
            degree=self._prompt_required_text("Degree"),
            grade=self._prompt_required_text("Grade"),
            start=self._prompt_required_text("Start"),
            end=self._prompt_optional_text("End"),
            location=self._prompt_required_text("Location"),
            relevant_coursework=self._prompt_list("Relevant coursework", required=True),
        )
        self._println(f"Staged new education entry '{item.name}'. Run 'apply' to save.")

    def _edit_education(self, index: int) -> None:
        item = self.session.get_education(index)
        updated = self.session.update_education(
            index,
            name=self._prompt_required_text("Name", default=item.name),
            degree=self._prompt_required_text("Degree", default=item.degree),
            grade=self._prompt_required_text("Grade", default=item.grade),
            start=self._prompt_required_text("Start", default=item.start),
            end=self._prompt_optional_editable_text("End", item.end),
            location=self._prompt_required_text("Location", default=item.location),
            relevant_coursework=self._prompt_editable_list(
                "Relevant coursework",
                item.relevant_coursework,
                required=True,
            ),
        )
        self._println(f"Staged updates for '{updated.name}'. Run 'apply' to save.")

    def _delete_education(self, index: int) -> None:
        item = self.session.get_education(index)
        if not self._confirm(
            f"Delete '{item.name}' from staged state?",
            default=False,
        ):
            self._println("Delete canceled.")
            return

        deleted = self.session.delete_education(index)
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
        self._println("Reloaded education evidence from disk.")

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
        return super()._parse_single_index(parts, command, "Education")

    def _print_pending_changes(self, changes: PendingEducationChanges) -> None:
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
