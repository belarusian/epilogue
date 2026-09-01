"""epilogue — render release-note-style changelogs from a project cycle log.

This bootstrap cycle ships only the data model. The parse-to-render-to-CLI
capability is a later build cycle.

Public API (re-exported from :mod:`epilogue.model`):
    * :class:`MergeStatus` — three-way merge classification enum.
    * :class:`Entry` — a single log line-item.
    * :class:`Cycle` — a ``## Cycle N`` block.
"""

from __future__ import annotations

from epilogue.model import Cycle, Entry, MergeStatus

__version__ = "0.1.0"

__all__ = [
    "Cycle",
    "Entry",
    "MergeStatus",
    "__version__",
]
