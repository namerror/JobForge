from __future__ import annotations

import builtins
import sys
from typing import Callable, TextIO


class EvidenceCLIBase:
    prompt_label = "evidence"

    def __init__(
        self,
        *,
        input_func: Callable[[str], str] = input,
        output: TextIO | None = None,
    ):
        self.input_func = input_func
        self.output = output or sys.stdout

    def run(self) -> int:
        self._println(f"{self.prompt_label.capitalize()} evidence CLI. Type 'help' for commands.")

        while True:
            try:
                raw_command = self.input_func(f"{self.prompt_label}> ").strip()
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
        raise NotImplementedError

    def _prompt_required_text(self, label: str, default: str | None = None) -> str:
        while True:
            value = self._prompt_value(label, default=default).strip()
            if value:
                return value
            self._println(f"{label} is required.")

    def _prompt_optional_text(self, label: str, default: str | None = None) -> str | None:
        value = self._prompt_value(label, default=default).strip()
        return value or None

    def _prompt_optional_editable_text(self, label: str, current_value: str | None) -> str | None:
        current = current_value or "none"
        self._println(f"Current {label}: {current}")
        if self._confirm(f"Keep current {label.lower()}?", default=True):
            return current_value
        return self._prompt_optional_text(label)

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

    def _prompt_comma_list(
        self,
        label: str,
        *,
        default_items: list[str] | None = None,
        required: bool = False,
    ) -> list[str]:
        default = self._format_comma_list(default_items) if default_items is not None else None

        while True:
            raw_value = self._prompt_value(label, default=default)
            try:
                return self._parse_comma_list(label, raw_value, required=required)
            except ValueError as exc:
                self._println(f"Error: {exc}")

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
        if default is not None and self.input_func is builtins.input:
            return self._prompt_value_with_prefill(label, default)

        if default is None:
            prompt = f"{label}: "
        else:
            prompt = f"{label} [{default}]: "
        value = self.input_func(prompt)
        return value if value else (default or "")

    def _prompt_value_with_prefill(self, label: str, default: str) -> str:
        try:
            import readline
        except ImportError:
            value = self.input_func(f"{label} [{default}]: ")
            return value if value else default

        readline.set_startup_hook(lambda: readline.insert_text(default))
        try:
            return self.input_func(f"{label}: ")
        finally:
            readline.set_startup_hook()

    def _format_comma_list(self, items: list[str] | None) -> str:
        return ", ".join(items or [])

    def _parse_comma_list(self, label: str, raw_value: str, required: bool = False) -> list[str]:
        if not raw_value.strip():
            if required:
                raise ValueError(f"At least one {label.lower()} item is required.")
            return []

        items = [item.strip() for item in raw_value.split(",")]
        if any(not item for item in items):
            raise ValueError(f"{label} cannot contain empty comma-separated items.")
        return items

    def _show_list(self, label: str, items: list[str]) -> None:
        if not items:
            self._println(f"{label}: none")
            return
        self._println(f"{label}: {', '.join(items)}")

    def _show_optional_text(self, label: str, value: str | None) -> None:
        self._println(f"{label}: {value or 'none'}")

    def _show_indexed_list(self, label: str, items: list[str]) -> None:
        if not items:
            self._println(f"{label}: none")
            return
        self._println(f"{label}:")
        for index, item in enumerate(items, start=1):
            self._println(f"  {index}. {item}")

    def _parse_single_index(self, parts: list[str], command: str, label: str) -> int:
        if len(parts) != 2:
            raise ValueError(f"Usage: {command} <index>")
        try:
            return int(parts[1])
        except ValueError as exc:
            raise ValueError(f"{label} index must be an integer for '{command}'") from exc

    def _println(self, message: str) -> None:
        self.output.write(f"{message}\n")
