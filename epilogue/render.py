"""Renderer for epilogue cycle logs.

This module turns a parsed ``list[Cycle]`` into release-note-style changelog
text (``render``) or a machine-readable JSON document (``render_json``). Both
are pure, stdlib-only, fully-typed functions: no I/O, no argparse, no file
reads. The CLI (a later build cycle) and the tests share these surfaces.

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

Status selector
---------------
:func:`filter_by_status(cycles, status)` is a pure, stdlib-only selector
that returns a NEW list of NEW :class:`Cycle` objects containing only the
entries whose ``status is status``; cycles with no matching entry are
dropped. It never mutates its input and never raises.
"""

from __future__ import annotations

import json

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


def render_json(cycles: list[Cycle], *, project: str | None = None) -> str:
    """Render a list of :class:`Cycle` into a machine-readable JSON document.

    This is the structured counterpart to :func:`render`. It is pure,
    stdlib-only, and fully typed: no I/O, no argparse. The CLI and the tests
    share this one surface.

    The returned document is a ``str`` (via :func:`json.dumps`) encoding an
    object with:

    * an optional ``"project"`` key — present only when ``project`` is not
      ``None`` (the literal string ``"None"`` is never emitted);
    * a ``"cycles"`` array, one object per cycle, in the given order.

    Each cycle object carries ``"number"`` (int), ``"title"`` (str), and
    ``"entries"`` (an array of ``{"description", "status"}`` objects, in the
    entry's original order). ``"status"`` is the :class:`MergeStatus` enum's
    ``.value`` string (``"merged"`` / ``"no_op"`` / ``"not_merged"``), so the
    three-way distinction is preserved as a stable, machine-checkable token.

    Args:
        cycles: The cycles to render, in the order they should appear.
        project: Optional project name. When provided it is emitted as the
            ``"project"`` key; when ``None`` the key is omitted entirely.

    Returns:
        A JSON document as a ``str``. An empty ``cycles`` list yields
        ``{"cycles": []}`` (plus ``"project"`` when given) and never raises.
    """
    doc: dict[str, object] = {}
    if project is not None:
        doc["project"] = project
    doc["cycles"] = [
        {
            "number": cycle.number,
            "title": cycle.title,
            "entries": [
                {"description": entry.description, "status": entry.status.value}
                for entry in cycle.entries
            ],
        }
        for cycle in cycles
    ]
    return json.dumps(doc)


def filter_by_status(cycles: list[Cycle], status: MergeStatus) -> list[Cycle]:
    """Filter a list of :class:`Cycle` down to entries of one :class:`MergeStatus`.

    This is a pure, stdlib-only, fully-typed selector: it returns a NEW list of
    NEW :class:`Cycle` objects and never mutates the input list or its cycles.
    Each returned cycle keeps its ``number`` and ``title`` but contains ONLY the
    entries whose ``entry.status is status``. Any cycle with zero matching
    entries is dropped entirely. Cycle order and, within a cycle, entry order
    are preserved.

    Args:
        cycles: The cycles to filter, in the order they should appear.
        status: The single :class:`MergeStatus` to keep.

    Returns:
        A new list of new :class:`Cycle` objects holding only the matching
        entries, with cycles that have no matching entry dropped. An empty
        ``cycles`` input returns ``[]``. It never raises.
    """
    result: list[Cycle] = []
    for cycle in cycles:
        matching = [entry for entry in cycle.entries if entry.status is status]
        if not matching:
            continue
        result.append(
            Cycle(number=cycle.number, title=cycle.title, entries=matching)
        )
    return result
