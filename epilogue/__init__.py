"""epilogue — render release-note-style changelogs from a project cycle log.

This build cycle ships the data model, the cycle-log parser, and the CLI
shell. The CLI shell exists and is testable, but the parse-to-render
capability is still pending (a later build cycle): the CLI does not yet wire
the parser into a renderer.

Public API (re-exported from :mod:`epilogue.model` and
:mod:`epilogue.parser`):
    * :class:`MergeStatus` — three-way merge classification enum.
    * :class:`Entry` — a single log line-item.
    * :class:`Cycle` — a ``## Cycle N`` block.
    * :func:`parse_log` — parse a raw cycle log into a list of :class:`Cycle`.
"""

from __future__ import annotations

from epilogue.model import Cycle, Entry, MergeStatus
from epilogue.parser import parse_log

__version__ = "0.1.0"

__all__ = [
    "Cycle",
    "Entry",
    "MergeStatus",
    "parse_log",
    "__version__",
]
