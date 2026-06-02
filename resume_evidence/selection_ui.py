from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from typing import TypeVar

PickerFunc = Callable[[str, Sequence[str]], int | None]
ChoiceValue = TypeVar("ChoiceValue")
ChoiceFunc = Callable[[str, Sequence[tuple[ChoiceValue | None, str]]], ChoiceValue | None]


def choose_index(message: str, labels: Sequence[str]) -> int | None:
    """Return a selected one-based index, or None when selection is unavailable."""
    if not labels or not sys.stdin.isatty():
        return None

    try:
        from prompt_toolkit.shortcuts import choice
    except ImportError:
        return None

    options = [(index, label) for index, label in enumerate(labels, start=1)]

    try:
        selected = choice(
            message=message,
            options=options,
            default=1,
            bottom_toolbar="Use Up/Down to choose, Enter to select.",
        )
    except (EOFError, KeyboardInterrupt):
        return None

    return selected if isinstance(selected, int) else None


def choose_value(
    message: str,
    choices: Sequence[tuple[ChoiceValue | None, str]],
) -> ChoiceValue | None:
    """Return the selected choice value, or None when selection is unavailable or canceled."""
    if not choices or not sys.stdin.isatty():
        return None

    try:
        from prompt_toolkit.shortcuts import choice
    except ImportError:
        return None

    try:
        return choice(
            message=message,
            options=choices,
            default=choices[0][0],
            bottom_toolbar="Use Up/Down to choose, Enter to select, Ctrl+C to use command line.",
        )
    except (EOFError, KeyboardInterrupt):
        return None
