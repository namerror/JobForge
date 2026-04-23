from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path
from typing import Callable, TextIO

from app.resume_evidence.session import PendingProjectChanges, ProjectsEvidenceSession


class ProjectsEvidenceCLI:
    def __init__(
        self,
        session: ProjectsEvidenceSession,
        *,
        input_func: Callable[[str], str] = input,
        output: TextIO | None = None,
    ):
        self.session = session
        self.input_func = input_func
        self.output = output or sys.stdout

    def run(self) -> int:
        self._println("Projects evidence CLI. Type 'help' for commands.")

        while True:
            try:
                raw_command = self.input_func("projects> ").strip()
            except EOFError:
                if self._handle_quit():
                    continue
                return 0
            except KeyboardInterrupt:
                self._println("\nInterrupted. Type 'quit' to exit.")
                continue

            if not raw_command:
                continue

            try:
                should_continue = self.execute(raw_command)
            except ValueError as exc:
                self._println(f"Error: {exc}")
                should_continue = True
            except IndexError as exc:
                self._println(f"Error: {exc}")
                should_continue = True

            if not should_continue:
                return 0

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
            index = self._parse_single_index(parts, "show")
            self._show_project(index)
            return True
        if command == "create":
            self._create_project()
            return True
        if command == "edit":
            index = self._parse_single_index(parts, "edit")
            self._edit_project(index)
            return True
        if command == "delete":
            index = self._parse_single_index(parts, "delete")
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
        self._println("  show <index>   Show a staged project")
        self._println("  create         Create a new staged project")
        self._println("  edit <index>   Edit an existing staged project")
        self._println("  delete <index> Delete a staged project")
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
            technology=self._prompt_list("Technology skills"),
            programming=self._prompt_list("Programming skills"),
            concepts=self._prompt_list("Concepts"),
            links=self._prompt_optional_list("Links"),
        )
        self._println(f"Staged new project '{project.name}'. Run 'apply' to save.")

    def _edit_project(self, index: int) -> None:
        project = self.session.get_project(index)
        updated = self.session.update_project(
            index,
            name=self._prompt_required_text("Name", default=project.name),
            summary=self._prompt_required_text("Summary", default=project.summary),
            highlights=self._prompt_editable_list("Highlights", project.highlights, required=True),
            active=self._prompt_bool("Active", default=project.active),
            technology=self._prompt_editable_list("Technology skills", project.skills.technology),
            programming=self._prompt_editable_list("Programming skills", project.skills.programming),
            concepts=self._prompt_editable_list("Concepts", project.skills.concepts),
            links=self._prompt_optional_editable_list("Links", project.links),
        )
        self._println(f"Staged updates for '{updated.name}'. Run 'apply' to save.")

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

    def _prompt_required_text(self, label: str, default: str | None = None) -> str:
        while True:
            value = self._prompt_value(label, default=default).strip()
            if value:
                return value
            self._println(f"{label} is required.")

    def _prompt_list(self, label: str, required: bool = False) -> list[str]:
        self._println(f"{label}: enter one item per line. Leave blank to finish.")
        items: list[str] = []

        while True:
            item = self.input_func("> ").strip()
            if not item:
                if required and not items:
                    self._println(f"At least one {label.lower()} item is required.")
                    continue
                return items
            items.append(item)

    def _prompt_optional_list(self, label: str) -> list[str] | None:
        items = self._prompt_list(label)
        return items or None

    def _prompt_editable_list(
        self,
        label: str,
        current_items: list[str],
        required: bool = False,
    ) -> list[str]:
        self._show_list(f"Current {label}", current_items)
        if self._confirm(f"Keep current {label.lower()}?", default=True):
            return list(current_items)
        return self._prompt_list(label, required=required)

    def _prompt_optional_editable_list(
        self,
        label: str,
        current_items: list[str] | None,
    ) -> list[str] | None:
        current = current_items or []
        self._show_list(f"Current {label}", current)
        if self._confirm(f"Keep current {label.lower()}?", default=True):
            return list(current_items) if current_items is not None else None
        return self._prompt_optional_list(label)

    def _prompt_bool(self, label: str, default: bool) -> bool:
        suffix = "[Y/n]" if default else "[y/N]"
        while True:
            raw_value = self.input_func(f"{label} {suffix}: ").strip().lower()
            if not raw_value:
                return default
            if raw_value in {"y", "yes"}:
                return True
            if raw_value in {"n", "no"}:
                return False
            self._println("Please enter yes or no.")

    def _confirm(self, message: str, default: bool) -> bool:
        return self._prompt_bool(message, default=default)

    def _prompt_value(self, label: str, default: str | None = None) -> str:
        if default is None:
            prompt = f"{label}: "
        else:
            prompt = f"{label} [{default}]: "
        value = self.input_func(prompt)
        return value if value else (default or "")

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

    def _show_list(self, label: str, items: list[str]) -> None:
        if not items:
            self._println(f"{label}: none")
            return
        self._println(f"{label}: {', '.join(items)}")

    def _println(self, message: str) -> None:
        self.output.write(f"{message}\n")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Interactive CLI for projects resume evidence.")
    parser.add_argument(
        "--path",
        type=Path,
        default=None,
        help="Optional path to a projects.yaml file. Defaults to user/resume_evidence/projects.yaml.",
    )
    return parser


def main(
    argv: list[str] | None = None,
    *,
    input_func: Callable[[str], str] = input,
    output: TextIO | None = None,
) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    session = ProjectsEvidenceSession.load(args.path)
    cli = ProjectsEvidenceCLI(session, input_func=input_func, output=output)
    return cli.run()


if __name__ == "__main__":
    raise SystemExit(main())
