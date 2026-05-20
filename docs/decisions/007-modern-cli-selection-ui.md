# 007 - Modern CLI Selection UI

Date: 2026-05-20

## Status

Pending

## Context

The resume evidence CLI currently uses command prompts and numeric indices for selecting
projects and project highlights. This is deterministic, easy to test, and dependency-light,
but editing longer lists still requires users to type commands such as `edit 3` or
`delete 2`.

A smoother future experience could let users move through projects or highlights with the
up/down arrow keys, show a highlighted active row, and confirm the selected item before
editing. This could reduce typing and make repeated evidence edits feel more modern.

## Decision

Consider a focused `prompt_toolkit` based selection layer as the preferred future direction.
This would add reusable picker/edit widgets for project and highlight selection while
keeping the existing command REPL as a fallback.

The first implementation should be limited to:

- Choosing a project from the staged project list.
- Choosing a highlight within a project.
- Returning selected one-based indices into the current session logic.
- Preserving the existing YAML schemas and staged session APIs.

Estimated implementation size is roughly 250-500 lines of application code and tests for a
small reusable picker. A broader full-screen TUI using Textual or raw curses is possible,
but likely too large for the current project scope at roughly 700-1200+ lines plus more
interaction testing and terminal compatibility handling.

## Consequences

### Positive

- Users can select projects and highlights with fewer keystrokes.
- Selection behavior can be reused across project and highlight workflows.
- The existing command mode can remain available for deterministic scripts and fallback.

### Negative

- Adds a new runtime dependency if implemented.
- Terminal UI behavior is harder to unit test than simple prompt parsing.
- More care is needed for non-interactive environments and accessibility.

### Neutral

- Evidence schemas do not change.
- Session and validation logic should remain command-agnostic.
- This ADR does not authorize implementation yet; it records a pending direction.

## Alternatives Considered

- Keep command-only editing: simplest and most testable, but less ergonomic for repeated
  list edits.
- Use raw `curses`: avoids a richer third-party abstraction but requires more terminal
  compatibility code.
- Use Textual: powerful for full-screen interfaces, but heavier than needed for focused
  project/highlight selection.
