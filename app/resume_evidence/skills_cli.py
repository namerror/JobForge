from __future__ import annotations
from typing import Callable, TextIO
import shlex

from app.resume_evidence.base_cli import EvidenceCLIBase
from app.resume_evidence.session import SkillsEvidenceSession, PendingSkillsChanges

class SkillsEvidenceCLI(EvidenceCLIBase):
    prompt_label = "skills"

    def __init__(
        self,
        session: SkillsEvidenceSession,
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
            self._list_skills()
            return True
        if command == "edit":
            self._edit_skills()
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
        self._println("  list           Show staged skills by category")
        self._println("  edit           Edit staged skills")
        self._println("  apply          Save staged changes to disk")
        self._println("  reload         Discard staged changes and reload from disk")
        self._println("  quit           Exit the CLI")

    def _list_skills(self) -> None:
        skills_file = self.session.get_skills()
        self._show_list("Technology", skills_file.skills.technology)
        self._show_list("Programming", skills_file.skills.programming)
        self._show_list("Concepts", skills_file.skills.concepts)

        if self.session.dirty:
            self._println("Staged changes are pending. Run 'apply' to write them to disk.")

    def _edit_skills(self) -> None:
        skills_file = self.session.get_skills()
        self.session.update_skills(
            technology=self._prompt_comma_list(
                "Technology skills",
                default_items=skills_file.skills.technology,
            ),
            programming=self._prompt_comma_list(
                "Programming skills",
                default_items=skills_file.skills.programming,
            ),
            concepts=self._prompt_comma_list(
                "Concepts",
                default_items=skills_file.skills.concepts,
            ),
        )
        self._println("Staged skills updates. Run 'apply' to save.")

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
        self._println("Reloaded skills evidence from disk.")

    def _handle_quit(self) -> bool:
        if self.session.dirty and not self._confirm(
            "Discard unapplied changes and quit?",
            default=False,
        ):
            self._println("Quit canceled.")
            return True

        self._println("Goodbye.")
        return False

    def _print_pending_changes(self, changes: PendingSkillsChanges) -> None:
        self._println(f"Pending changes: {len(changes.changed_categories)} categories updated.")
        if changes.changed_categories:
            self._println(f"Updated categories: {', '.join(changes.changed_categories)}")
