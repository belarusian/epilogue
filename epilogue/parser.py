"""Parser for epilogue cycle logs.

This module turns a raw project cycle log (plain text) into a list of
:class:`~epilogue.model.Cycle` objects. It is a pure, stdlib-only function:
no I/O, no argparse, no file reads. The CLI and renderer are separate build
cycles and are intentionally not touched here.

Header grammar
--------------
Cycles are delimited by lines of the form::

    ## Cycle N: <title>

where ``N`` is a non-negative integer and ``<title>`` is the rest of the
line (which may be empty). Everything before the first such header is
ignored (preamble). A new header starts a new cycle; cycles are returned in
file order.

Line items
----------
Within a cycle, every non-blank line that is not itself a cycle header
becomes an :class:`~epilogue.model.Entry`. A leading bullet marker (``- ``
or ``* ``) is stripped; the remainder is the entry's ``description``. Plain
non-blank lines (no bullet) are used as-is. Blank lines are skipped.

Status inference (truthful, deterministic)
------------------------------------------
Each entry's :class:`~epilogue.model.MergeStatus` is inferred from its
description using a fixed, case-insensitive substring match against the
marker sets below. Precedence is ``NOT_MERGED`` > ``NO_OP`` > ``MERGED``
(default). The exact marker set is:

* ``NOT_MERGED`` markers (any one present -> ``NOT_MERGED``):
    - ``"not merged"``
    - ``"reverted"``
    - ``"abandoned"``
* ``NO_OP`` markers (any one present -> ``NO_OP``):
    - ``"no-op"``   (also matches ``"no-op:"``)
    - ``"no change"``
* ``MERGED``: the default when no ``NOT_MERGED`` or ``NO_OP`` marker is
  present.

Because matching is a case-insensitive substring test, ``"NOT MERGED"``,
``"Not Merged"``, ``"reverted"``, ``"abandoned"``, ``"no-op"``,
``"no-op:"``, and ``"no change"`` all classify deterministically.
"""

from __future__ import annotations

import re

from epilogue.model import Cycle, Entry, MergeStatus

# A cycle header: "## Cycle N: <title>" (N is an integer, title is the rest
# of the line, possibly empty). Anchored to the start of the line.
_CYCLE_HEADER_RE = re.compile(r"^##\s+Cycle\s+(\d+)\s*:\s*(.*)$")

# Bullet prefixes stripped from line items.
_BULLET_PREFIXES = ("- ", "* ")

# Deterministic, case-insensitive status markers. Precedence is
# NOT_MERGED > NO_OP > MERGED (default). Documented in the module docstring.
_NOT_MERGED_MARKERS = ("not merged", "reverted", "abandoned")
_NO_OP_MARKERS = ("no-op", "no change")


def _strip_bullet(line: str) -> str:
    """Return the line with a leading bullet marker (``- `` / ``* ``) removed.

    The line is stripped of surrounding whitespace first. If it begins with a
    bullet prefix, that prefix is removed and the remainder re-stripped.
    """
    stripped = line.strip()
    for prefix in _BULLET_PREFIXES:
        if stripped.startswith(prefix):
            return stripped[len(prefix):].strip()
    return stripped


def _infer_status(description: str) -> MergeStatus:
    """Infer the truthful :class:`MergeStatus` from a description.

    Uses a case-insensitive substring match against the documented marker
    sets with precedence ``NOT_MERGED`` > ``NO_OP`` > ``MERGED``.
    """
    lowered = description.lower()
    for marker in _NOT_MERGED_MARKERS:
        if marker in lowered:
            return MergeStatus.NOT_MERGED
    for marker in _NO_OP_MARKERS:
        if marker in lowered:
            return MergeStatus.NO_OP
    return MergeStatus.MERGED


def parse_log(text: str) -> list[Cycle]:
    """Parse a raw cycle log into an ordered list of :class:`Cycle`.

    Args:
        text: The full text of a project cycle log.

    Returns:
        The cycles in file order. Text that is empty or whitespace-only (or
        contains no cycle header) returns an empty list. Everything before
        the first ``## Cycle N: <title>`` header is ignored.
    """
    cycles: list[Cycle] = []
    current: Cycle | None = None

    for raw_line in text.splitlines():
        header = _CYCLE_HEADER_RE.match(raw_line)
        if header is not None:
            current = Cycle(
                number=int(header.group(1)),
                title=header.group(2).strip(),
            )
            cycles.append(current)
            continue

        # Before the first header there is no cycle to attach entries to.
        if current is None:
            continue

        # Blank lines carry no entry.
        if not raw_line.strip():
            continue

        description = _strip_bullet(raw_line)
        if not description:
            continue

        current.entries.append(
            Entry(description=description, status=_infer_status(description))
        )

    return cycles
