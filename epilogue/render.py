"""Renderer for epilogue cycle logs.

This module turns a parsed ``list[Cycle]`` into release-note-style changelog
text. It is a pure, stdlib-only, fully-typed function: no I/O, no argparse,
no file reads. The CLI (a later build cycle) and the tests share this one
surface.

Rendering convention
--------------------
``render(cycles, *, project=None)`` returns a single ``str`` built as
``"\\n".join(lines) + "\\n"`` where ``lines`` is assembled as follows.

Empty input
    If ``cycles`` is empty, the result is the single line ``"No cycles."``
    (plus the trailing newline). It never raises.

Non-empty input
    * If ``project`` is not ``None``, the first line is ``"# " + project``
      (a top-level title). If ``project`` is ``None``, no title line is
      emitted at all — the literal string ``"None"`` is never printed.
    * For each cycle, in the given order, a section header line is emitted:
      ``"## Cycle <number>: <title>"`` (exactly that format; an empty title
      yields ``"## Cycle <number>: "``).
    * A blank line follows the cycle header.
    * Within the cycle, its entries are grouped by :class:`MergeStatus` into
      three sub-sections in this FIXED order: ``MERGED``, ``NO_OP``,
      ``NOT_MERGED``. A sub-section is emitted only if it has at least one
      entry (empty sub-sections are never emitted). The sub-section header
      lines are exactly ``"### Merged"``, ``"### No-ops"``, and
      ``"### Not Merged"``. Under each sub-section, each entry is listed as a
      line ``"- <description>"`` in the entry's original order.
    * A blank line follows the cycle's last sub-section, so consecutive
      cycles are visually separated.

The three statuses are kept TRUTHFULLY distinguishable in the output: a
reader can tell ``MERGED`` from ``NO_OP`` from ``NOT_MERGED`` at a glance,
because each lands under its own labeled sub-section. They are never
collapsed.
"""

from __future__ import annotations

from epilogue.model import Cycle, MergeStatus

# Fixed sub-section order and their exact header lines. The three-way
# distinction is the core truthfulness requirement, so the order and labels
# are pinned here and never reordered or merged.
_SECTION_ORDER: tuple[tuple[MergeStatus, str], ...] = (
    (MergeStatus.MERGED, "### Merged"),
    (MergeStatus.NO_OP, "### No-ops"),
    (MergeStatus.NOT_MERGED, "### Not Merged"),
)


def render(cycles: list[Cycle], *, project: str | None = None) -> str:
    """Render a list of :class:`Cycle` into release-note-style changelog text.

    Args:
        cycles: The cycles to render, in the order they should appear.
        project: Optional project name. When provided, it is emitted as a
            top-level ``"# <project>"`` title line; when ``None``, no title
            line is emitted (the literal string ``"None"`` is never printed).

    Returns:
        The rendered changelog as a single ``str`` ending in a newline. An
        empty ``cycles`` list returns ``"No cycles.\\n"`` and never raises.
    """
    if not cycles:
        return "No cycles.\n"

    lines: list[str] = []
    if project is not None:
        lines.append(f"# {project}")

    for cycle in cycles:
        lines.append(f"## Cycle {cycle.number}: {cycle.title}")

        subsection_lines: list[str] = []
        for status, header in _SECTION_ORDER:
            entries = [entry for entry in cycle.entries if entry.status is status]
            if not entries:
                continue
            subsection_lines.append(header)
            for entry in entries:
                subsection_lines.append(f"- {entry.description}")

        if subsection_lines:
            lines.append("")
            lines.extend(subsection_lines)
            lines.append("")
        else:
            lines.append("")

    return "\n".join(lines) + "\n"
