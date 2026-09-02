"""Data model for epilogue.

This module defines the core, stdlib-only data structures that the rest of
the build order grows on: a three-way :class:`MergeStatus` enum and the
:class:`Entry` / :class:`Cycle` dataclasses.

It intentionally contains no parsing, rendering, or CLI logic — those are
later build cycles. Everything here is plain ``dataclasses`` and ``enum``
from the standard library.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class MergeStatus(Enum):
    """Truthful three-way classification of a log entry.

    The distinction between these three states is the core truthfulness
    requirement of the project: an entry that was actually merged, an entry
    that was a no-op, and an entry that was NOT merged.
    """

    MERGED = "merged"
    NO_OP = "no_op"
    NOT_MERGED = "not_merged"


@dataclass
class Entry:
    """A single line-item within a cycle.

    Attributes:
        description: Human-readable description of what the entry did.
        status: The truthful merge classification of the entry (the primary
            status, chosen by the documented precedence
            ``NOT_MERGED`` > ``NO_OP`` > ``MERGED``).
        secondary_status: When the description carries markers of more than
            one status class, the primary ``status`` is still chosen by the
            precedence rule, but the *other* class is no longer silently
            dropped: it is recorded here. ``None`` when the description
            carries at most one status class (the common case). This is
            additive and never changes ``status``.
    """

    description: str
    status: MergeStatus
    secondary_status: MergeStatus | None = None


@dataclass
class Cycle:
    """A single ``## Cycle N`` block in a project log.

    Attributes:
        number: The cycle number (the ``N`` in ``## Cycle N``).
        title: The cycle title.
        entries: The ordered list of entries belonging to this cycle.
    """

    number: int
    title: str
    entries: list[Entry] = field(default_factory=list)
