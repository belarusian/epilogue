"""Tests for the epilogue cycle-log parser (pure, stdlib-only).

All log fixtures are small inline strings; no real log file is read.
"""

from __future__ import annotations

from epilogue.model import Cycle, Entry, MergeStatus
from epilogue.parser import parse_log


def test_multi_cycle_all_three_statuses() -> None:
    """A multi-cycle log yields exact Cycle/Entry structure and statuses."""
    log = (
        "## Cycle 1: Bootstrap\n"
        "- added the data model\n"
        "wired up the package\n"
        "* a no-op: nothing changed\n"
        "- this one was reverted\n"
        "\n"
        "## Cycle 2: Build\n"
        "- shipped the CLI shell\n"
        "abandoned the renderer for now\n"
    )
    cycles = parse_log(log)

    assert len(cycles) == 2

    c1 = cycles[0]
    assert isinstance(c1, Cycle)
    assert c1.number == 1
    assert c1.title == "Bootstrap"
    assert c1.entries == [
        Entry(description="added the data model", status=MergeStatus.MERGED),
        Entry(description="wired up the package", status=MergeStatus.MERGED),
        Entry(description="a no-op: nothing changed", status=MergeStatus.NO_OP),
        Entry(description="this one was reverted", status=MergeStatus.NOT_MERGED),
    ]

    c2 = cycles[1]
    assert c2.number == 2
    assert c2.title == "Build"
    assert c2.entries == [
        Entry(description="shipped the CLI shell", status=MergeStatus.MERGED),
        Entry(description="abandoned the renderer for now", status=MergeStatus.NOT_MERGED),
    ]


def test_preamble_before_first_header_is_ignored() -> None:
    """Text before the first cycle header produces no cycles/entries."""
    log = (
        "# Project Log\n"
        "Some intro paragraph that is not a cycle.\n"
        "- a stray bullet in the preamble\n"
        "## Cycle 3: Real\n"
        "- first real entry\n"
    )
    cycles = parse_log(log)
    assert len(cycles) == 1
    assert cycles[0].number == 3
    assert cycles[0].title == "Real"
    assert cycles[0].entries == [
        Entry(description="first real entry", status=MergeStatus.MERGED)
    ]


def test_empty_text_returns_empty_list() -> None:
    """Empty and whitespace-only text returns []."""
    assert parse_log("") == []
    assert parse_log("   \n\t\n  ") == []


def test_no_header_returns_empty_list() -> None:
    """Text with no cycle header returns []."""
    assert parse_log("just some prose\n- a bullet\n") == []


def test_cycle_with_no_entries() -> None:
    """A cycle header with no following line items has an empty entries list."""
    log = (
        "## Cycle 5: Empty\n"
        "\n"
        "## Cycle 6: Filled\n"
        "- one entry\n"
    )
    cycles = parse_log(log)
    assert len(cycles) == 2
    assert cycles[0].number == 5
    assert cycles[0].title == "Empty"
    assert cycles[0].entries == []
    assert cycles[1].number == 6
    assert cycles[1].entries == [
        Entry(description="one entry", status=MergeStatus.MERGED)
    ]


def test_default_merged_when_no_marker() -> None:
    """An entry with no status marker defaults to MERGED."""
    log = "## Cycle 1: Default\n- plain description here\n"
    cycles = parse_log(log)
    assert cycles[0].entries == [
        Entry(description="plain description here", status=MergeStatus.MERGED)
    ]


def test_status_precedence_not_merged_over_no_op() -> None:
    """NOT_MERGED wins over NO_OP when both markers appear."""
    log = "## Cycle 1: P\n- no-op but reverted\n"
    cycles = parse_log(log)
    assert cycles[0].entries[0].status is MergeStatus.NOT_MERGED


def test_status_case_insensitive() -> None:
    """Markers match case-insensitively."""
    log = (
        "## Cycle 1: CI\n"
        "- NOT MERGED\n"
        "- No-Op\n"
        "- No Change\n"
    )
    cycles = parse_log(log)
    statuses = [e.status for e in cycles[0].entries]
    assert statuses == [
        MergeStatus.NOT_MERGED,
        MergeStatus.NO_OP,
        MergeStatus.NO_OP,
    ]
