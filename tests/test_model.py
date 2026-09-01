"""Tests for the epilogue data model (enum + dataclasses)."""

from __future__ import annotations

from dataclasses import fields

from epilogue.model import Cycle, Entry, MergeStatus


def test_merge_status_has_exactly_three_members() -> None:
    """The three-way distinction is the core truthfulness requirement."""
    members = {m.name for m in MergeStatus}
    assert members == {"MERGED", "NO_OP", "NOT_MERGED"}


def test_merge_status_values_are_distinct_strings() -> None:
    values = [m.value for m in MergeStatus]
    assert all(isinstance(v, str) for v in values)
    assert len(set(values)) == len(values)


def test_entry_fields() -> None:
    entry = Entry(description="did a thing", status=MergeStatus.MERGED)
    assert entry.description == "did a thing"
    assert entry.status is MergeStatus.MERGED
    names = {f.name for f in fields(Entry)}
    assert names == {"description", "status"}


def test_entry_is_mutable_dataclass() -> None:
    entry = Entry(description="a", status=MergeStatus.NO_OP)
    entry.status = MergeStatus.NOT_MERGED
    assert entry.status is MergeStatus.NOT_MERGED


def test_cycle_fields_and_default_entries() -> None:
    cycle = Cycle(number=1, title="Bootstrap")
    assert cycle.number == 1
    assert cycle.title == "Bootstrap"
    assert cycle.entries == []
    names = {f.name for f in fields(Cycle)}
    assert names == {"number", "title", "entries"}


def test_cycle_entries_default_is_not_shared() -> None:
    """Each Cycle must get its own entries list (default_factory)."""
    a = Cycle(number=1, title="a")
    b = Cycle(number=2, title="b")
    a.entries.append(Entry(description="x", status=MergeStatus.MERGED))
    assert a.entries != b.entries
    assert b.entries == []


def test_cycle_holds_entries() -> None:
    entries = [
        Entry(description="merged thing", status=MergeStatus.MERGED),
        Entry(description="no-op thing", status=MergeStatus.NO_OP),
        Entry(description="not merged thing", status=MergeStatus.NOT_MERGED),
    ]
    cycle = Cycle(number=7, title="Build", entries=entries)
    assert cycle.entries == entries
    assert [e.status for e in cycle.entries] == [
        MergeStatus.MERGED,
        MergeStatus.NO_OP,
        MergeStatus.NOT_MERGED,
    ]
