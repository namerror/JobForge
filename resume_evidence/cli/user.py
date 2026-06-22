from __future__ import annotations

import shlex
from typing import Callable, TextIO

from resume_evidence.cli.base import EvidenceCLIBase
from resume_evidence.session import PendingUserInfoChanges, UserInfoEvidenceSession


class UserInfoEvidenceCLI(EvidenceCLIBase):
    prompt_label = "user"

    def __init__(
        self,
        session: UserInfoEvidenceSession,
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
        if command in {"show", "list"}:
            self._show_user_info()
            return True
        if command == "edit":
            self._edit_user_info()
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
        self._println("  show           Show staged user info")
        self._println("  list           Alias for show")
        self._println("  edit           Edit staged user info")
        self._println("  apply          Save staged changes to disk")
        self._println("  reload         Discard staged changes and reload from disk")
        self._println("  quit           Exit the CLI")

    def _show_user_info(self) -> None:
        user_info = self.session.get_user_info()
        self._println(f"Name: {user_info.name}")
        self._println(f"Email: {user_info.email}")
        self._println(f"Phone: {user_info.phone}")
        self._show_optional_text("LinkedIn", user_info.linkedin)
        self._show_optional_text("GitHub", user_info.github)
        self._show_optional_text("Website", user_info.website)

        if self.session.dirty:
            self._println("Staged changes are pending. Run 'apply' to write them to disk.")

    def _edit_user_info(self) -> None:
        user_info = self.session.get_user_info()
        self.session.update_user_info(
            name=self._prompt_required_text("Name", default=user_info.name),
            email=self._prompt_required_text("Email", default=user_info.email),
            phone=self._prompt_required_text("Phone", default=user_info.phone),
            linkedin=self._prompt_optional_editable_text("LinkedIn", user_info.linkedin),
            github=self._prompt_optional_editable_text("GitHub", user_info.github),
            website=self._prompt_optional_editable_text("Website", user_info.website),
        )
        self._println("Staged user info updates. Run 'apply' to save.")

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
        self._println("Reloaded user evidence from disk.")

    def _handle_quit(self) -> bool:
        if self.session.dirty and not self._confirm(
            "Discard unapplied changes and quit?",
            default=False,
        ):
            self._println("Quit canceled.")
            return True

        self._println("Goodbye.")
        return False

    def _print_pending_changes(self, changes: PendingUserInfoChanges) -> None:
        self._println(f"Pending changes: {len(changes.changed_fields)} fields updated.")
        if changes.changed_fields:
            self._println(f"Updated fields: {', '.join(changes.changed_fields)}")
