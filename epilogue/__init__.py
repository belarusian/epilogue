"""epilogue — render release-note-style changelogs from a project cycle log.

This build cycle ships the data model, the cycle-log parser, the renderer,
and the CLI. The parse-to-render capability now SHIPS: the CLI reads a cycle
log, filters it to a requested cycle range, renders the changelog, and prints
it to stdout.

Public API (re-exported from :mod:`epilogue.model`, :mod:`epilogue.parser`,
and :mod:`epilogue.render`):
    * :class:`MergeStatus` — three-way merge classification enum.
    * :class:`Entry` — a single log line-item.
    * :class:`Cycle` — a ``## Cycle N`` block.
    * :func:`parse_log` — parse a raw cycle log into a list of :class:`Cycle`.
    * :func:`render` — render a list of :class:`Cycle` into changelog text.
    * :func:`render_json` — render a list of :class:`Cycle` into a JSON document.
"""

from __future__ import annotations

from epilogue.model import Cycle, Entry, MergeStatus
from epilogue.parser import parse_log
from epilogue.render import render, render_json

__version__ = "0.1.0"

__all__ = [
    "Cycle",
    "Entry",
    "MergeStatus",
    "parse_log",
    "render",
    "render_json",
    "__version__",
]
