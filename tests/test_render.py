"""Tests for the epilogue renderer (pure, stdlib-only).

All fixtures are small inline :class:`Cycle` / :class:`Entry` objects built
from :mod:`epilogue.model`; no real ground-truth log file is read. The tests
pin the exact rendering convention documented in :mod:`epilogue.render`, with
emphasis on the core truthfulness requirement: MERGED, NO_OP, and NOT_MERGED
must each be distinguishable in the output.
"""

from __future__ import annotations

from epilogue.model import Cycle, Entry, MergeStatus
from epilogue.render import render


def _cycle_block(text: str, number: int) -> list[str]:
    """Return the lines belonging to a given cycle (everything after its header).

    The block runs from just after the ``## Cycle <number>:`` header up to the
    next ``## Cycle`` header (or end of text). The trailing colon in the match
    disambiguates e.g. ``1`` from ``10``.
    """
    lines = text.splitlines()
    prefix = f"## Cycle {number}:"
    start = None
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            start = i + 1
            break
    assert start is not None, f"cycle {number} header not found in output"
    block: list[str] = []
    for line in lines[start:]:
        if line.startswith("## Cycle "):
            break
        block.append(line)
    return block


def _section_entries(block: list[str]) -> dict[str, list[str]]:
    """Map each ``### <header>`` sub-section to the ordered list of its entries.

    Only lines that are sub-section headers (``### ``) or entry bullets
    (``- ``) are considered; blank lines and the cycle header are ignored.
    """
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in block:
        if line.startswith("### "):
            current = line
            sections.setdefault(current, [])
        elif line.startswith("- ") and current is not None:
            sections[current].append(line[2:])
    return sections


def _all_three_cycles() -> list[Cycle]:
    """Two cycles whose combined entries cover all three statuses."""
    return [
        Cycle(
            number=1,
            title="Bootstrap",
            entries=[
                Entry(description="added the data model", status=MergeStatus.MERGED),
                Entry(description="a no-op: nothing changed", status=MergeStatus.NO_OP),
                Entry(description="this one was reverted", status=MergeStatus.NOT_MERGED),
                Entry(description="wired up the package", status=MergeStatus.MERGED),
            ],
        ),
        Cycle(
            number=2,
            title="Build",
            entries=[
                Entry(description="shipped the CLI shell", status=MergeStatus.MERGED),
                Entry(description="abandoned the renderer", status=MergeStatus.NOT_MERGED),
            ],
        ),
    ]


def test_multi_cycle_all_three_statuses_distinguishable() -> None:
    """Each status lands under its own labeled sub-section (never collapsed)."""
    text = render(_all_three_cycles())

    # All three sub-section headers are present and truthfully distinct.
    assert "### Merged" in text
    assert "### No-ops" in text
    assert "### Not Merged" in text

    c1 = _section_entries(_cycle_block(text, 1))
    assert c1["### Merged"] == ["added the data model", "wired up the package"]
    assert c1["### No-ops"] == ["a no-op: nothing changed"]
    assert c1["### Not Merged"] == ["this one was reverted"]

    c2 = _section_entries(_cycle_block(text, 2))
    assert c2["### Merged"] == ["shipped the CLI shell"]
    assert c2["### Not Merged"] == ["abandoned the renderer"]
    # Cycle 2 has no no-ops, so that sub-section must be absent.
    assert "### No-ops" not in c2


def test_empty_list_returns_no_cycles_and_does_not_raise() -> None:
    """``render([])`` returns the single 'No cycles.' line and never raises."""
    result = render([])
    assert result == "No cycles.\n"
    assert result.splitlines() == ["No cycles."]


def test_project_present_emits_title_line() -> None:
    """A provided project name becomes the first ``# <project>`` line."""
    text = render(_all_three_cycles(), project="demo")
    lines = text.splitlines()
    assert lines[0] == "# demo"
    # The title is the only single-hash line; cycles are '##', sub-sections '###'.
    single_hash = [line for line in lines if line.startswith("# ")]
    assert single_hash == ["# demo"]


def test_project_absent_has_no_title_and_no_literal_none() -> None:
    """Without a project there is no title line and 'None' never appears."""
    text = render(_all_three_cycles())
    lines = text.splitlines()
    # No single-hash title line (cycle headers are '##', sub-sections '###').
    assert not any(line.startswith("# ") for line in lines)
    assert "None" not in text


def test_single_cycle_with_no_entries_renders_header_only() -> None:
    """An empty cycle renders its header and no sub-sections at all."""
    text = render([Cycle(number=5, title="Empty", entries=[])])
    lines = text.splitlines()
    assert "## Cycle 5: Empty" in lines
    # No sub-section headers and no entry bullets.
    assert not any(line.startswith("### ") for line in lines)
    assert not any(line.startswith("- ") for line in lines)


def test_empty_subsections_are_never_emitted() -> None:
    """A cycle with only one status emits only that sub-section's header."""
    cycle = Cycle(
        number=3,
        title="Only Merged",
        entries=[
            Entry(description="first merged", status=MergeStatus.MERGED),
            Entry(description="second merged", status=MergeStatus.MERGED),
        ],
    )
    text = render([cycle])
    assert "### Merged" in text
    assert "### No-ops" not in text
    assert "### Not Merged" not in text


def test_entry_order_within_section_is_preserved() -> None:
    """Entries keep their original order inside each sub-section."""
    cycle = Cycle(
        number=1,
        title="Order",
        entries=[
            Entry(description="m1", status=MergeStatus.MERGED),
            Entry(description="m2", status=MergeStatus.MERGED),
            Entry(description="m3", status=MergeStatus.MERGED),
        ],
    )
    text = render([cycle])
    assert _section_entries(_cycle_block(text, 1))["### Merged"] == ["m1", "m2", "m3"]


def test_empty_title_header_keeps_trailing_space() -> None:
    """An empty title still yields the exact '## Cycle N: ' header format."""
    text = render([Cycle(number=3, title="", entries=[])])
    assert "## Cycle 3: " in text.splitlines()


def test_render_is_pure_and_returns_str() -> None:
    """Output is a str and is stable across repeated calls (pure function)."""
    cycles = _all_three_cycles()
    first = render(cycles, project="demo")
    second = render(cycles, project="demo")
    assert isinstance(first, str)
    assert first == second
    # Mutating the input list afterwards does not affect an already-built string.
    cycles.append(Cycle(number=9, title="Late", entries=[]))
    assert first == second
