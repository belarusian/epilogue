"""Tests for the epilogue renderer (pure, stdlib-only).

All fixtures are small inline :class:`Cycle` / :class:`Entry` objects built
from :mod:`epilogue.model`; no real ground-truth log file is read. The tests
pin the exact rendering convention documented in :mod:`epilogue.render`, with
emphasis on the core truthfulness requirement: MERGED, NO_OP, and NOT_MERGED
must each be distinguishable in the output.
"""

from __future__ import annotations

import json

from epilogue.model import Cycle, Entry, MergeStatus
from epilogue.render import filter_by_status, render, render_json


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


# ---------------------------------------------------------------------------
# render_json tests (TICKET-021)
# ---------------------------------------------------------------------------


def test_render_json_multi_cycle_all_three_statuses() -> None:
    """Each status lands as its own stable token; structure is exact."""
    doc = json.loads(render_json(_all_three_cycles(), project="demo"))

    assert doc["project"] == "demo"
    assert [c["number"] for c in doc["cycles"]] == [1, 2]
    assert [c["title"] for c in doc["cycles"]] == ["Bootstrap", "Build"]

    c1 = doc["cycles"][0]
    assert c1["entries"] == [
        {"description": "added the data model", "status": "merged"},
        {"description": "a no-op: nothing changed", "status": "no_op"},
        {"description": "this one was reverted", "status": "not_merged"},
        {"description": "wired up the package", "status": "merged"},
    ]
    c2 = doc["cycles"][1]
    assert c2["entries"] == [
        {"description": "shipped the CLI shell", "status": "merged"},
        {"description": "abandoned the renderer", "status": "not_merged"},
    ]

    # The three-way distinction is preserved as distinct tokens (truthfulness).
    all_statuses = [e["status"] for c in doc["cycles"] for e in c["entries"]]
    assert set(all_statuses) == {"merged", "no_op", "not_merged"}


def test_render_json_project_absent_key_is_omitted() -> None:
    """When project is None the 'project' key is ABSENT (never the string 'None')."""
    doc = json.loads(render_json(_all_three_cycles()))
    assert "project" not in doc
    assert "None" not in json.dumps(doc)
    assert doc["cycles"]  # cycles still present


def test_render_json_empty_cycles_is_well_defined() -> None:
    """Empty cycles -> {"cycles": []} (plus project when given); never raises."""
    assert json.loads(render_json([])) == {"cycles": []}
    assert json.loads(render_json([], project="demo")) == {
        "project": "demo",
        "cycles": [],
    }


def test_render_json_preserves_cycle_and_entry_order() -> None:
    """Cycle order and, within a cycle, entry order are preserved verbatim."""
    cycles = [
        Cycle(
            number=3,
            title="C",
            entries=[
                Entry(description="x", status=MergeStatus.MERGED),
                Entry(description="y", status=MergeStatus.NO_OP),
                Entry(description="z", status=MergeStatus.NOT_MERGED),
            ],
        ),
        Cycle(number=1, title="A", entries=[]),
    ]
    doc = json.loads(render_json(cycles))
    assert [c["number"] for c in doc["cycles"]] == [3, 1]
    assert [e["description"] for e in doc["cycles"][0]["entries"]] == ["x", "y", "z"]
    assert doc["cycles"][1]["entries"] == []


def test_render_json_returns_str_and_is_pure() -> None:
    """Output is a str and stable across repeated calls (pure function)."""
    cycles = _all_three_cycles()
    first = render_json(cycles, project="demo")
    second = render_json(cycles, project="demo")
    assert isinstance(first, str)
    assert first == second
    # Mutating the input afterwards does not affect an already-built string.
    cycles.append(Cycle(number=9, title="Late", entries=[]))
    assert first == second


# ---------------------------------------------------------------------------
# filter_by_status tests (TICKET-029)
# ---------------------------------------------------------------------------


def _filter_fixture() -> list[Cycle]:
    """Two cycles whose combined entries cover all three statuses.

    Cycle 1 has all three statuses; cycle 2 has only merged + not_merged
    (no no_op), so filtering by no_op must drop cycle 2 entirely.
    """
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


def test_filter_by_status_each_status_returns_only_matching_entries() -> None:
    """Filtering by each status keeps only matching entries, in order."""
    cycles = _filter_fixture()

    merged = filter_by_status(cycles, MergeStatus.MERGED)
    assert [c.number for c in merged] == [1, 2]
    assert [e.description for e in merged[0].entries] == [
        "added the data model",
        "wired up the package",
    ]
    assert [e.description for e in merged[1].entries] == ["shipped the CLI shell"]
    assert all(e.status is MergeStatus.MERGED for c in merged for e in c.entries)

    no_op = filter_by_status(cycles, MergeStatus.NO_OP)
    # Only cycle 1 has a no_op; cycle 2 is dropped.
    assert [c.number for c in no_op] == [1]
    assert [e.description for e in no_op[0].entries] == ["a no-op: nothing changed"]
    assert all(e.status is MergeStatus.NO_OP for c in no_op for e in c.entries)

    not_merged = filter_by_status(cycles, MergeStatus.NOT_MERGED)
    assert [c.number for c in not_merged] == [1, 2]
    assert [e.description for e in not_merged[0].entries] == ["this one was reverted"]
    assert [e.description for e in not_merged[1].entries] == ["abandoned the renderer"]
    assert all(e.status is MergeStatus.NOT_MERGED for c in not_merged for e in c.entries)


def test_filter_by_status_drops_cycles_with_no_matching_entry() -> None:
    """A cycle with zero matching entries is dropped entirely."""
    cycles = [
        Cycle(
            number=1,
            title="Only Merged",
            entries=[Entry(description="m", status=MergeStatus.MERGED)],
        ),
        Cycle(number=2, title="Empty", entries=[]),
    ]
    result = filter_by_status(cycles, MergeStatus.NOT_MERGED)
    assert result == []
    # Even the empty cycle is dropped (it has no matching entry).
    result_merged = filter_by_status(cycles, MergeStatus.MERGED)
    assert [c.number for c in result_merged] == [1]


def test_filter_by_status_preserves_cycle_and_entry_order() -> None:
    """Cycle order and, within a cycle, entry order are preserved verbatim."""
    cycles = [
        Cycle(
            number=3,
            title="C",
            entries=[
                Entry(description="z", status=MergeStatus.MERGED),
                Entry(description="y", status=MergeStatus.MERGED),
                Entry(description="x", status=MergeStatus.MERGED),
            ],
        ),
        Cycle(
            number=1,
            title="A",
            entries=[Entry(description="a", status=MergeStatus.MERGED)],
        ),
    ]
    result = filter_by_status(cycles, MergeStatus.MERGED)
    assert [c.number for c in result] == [3, 1]
    assert [e.description for e in result[0].entries] == ["z", "y", "x"]
    assert [e.description for e in result[1].entries] == ["a"]


def test_filter_by_status_does_not_mutate_input() -> None:
    """The original cycles and their entries are unchanged after the call."""
    cycles = _filter_fixture()
    original_numbers = [c.number for c in cycles]
    original_titles = [c.title for c in cycles]
    original_entry_counts = [len(c.entries) for c in cycles]
    original_descriptions = [
        [e.description for e in c.entries] for c in cycles
    ]

    filter_by_status(cycles, MergeStatus.MERGED)
    filter_by_status(cycles, MergeStatus.NO_OP)
    filter_by_status(cycles, MergeStatus.NOT_MERGED)

    assert [c.number for c in cycles] == original_numbers
    assert [c.title for c in cycles] == original_titles
    assert [len(c.entries) for c in cycles] == original_entry_counts
    assert [[e.description for e in c.entries] for c in cycles] == original_descriptions


def test_filter_by_status_empty_input_returns_empty_list() -> None:
    """An empty input list returns [] and never raises."""
    assert filter_by_status([], MergeStatus.MERGED) == []
    assert filter_by_status([], MergeStatus.NO_OP) == []
    assert filter_by_status([], MergeStatus.NOT_MERGED) == []


def test_filter_by_status_returns_new_cycle_objects() -> None:
    """Returned cycles are NEW objects, not the same as the input cycles."""
    cycles = _filter_fixture()
    result = filter_by_status(cycles, MergeStatus.MERGED)
    assert result
    for returned, original in zip(result, cycles):
        assert returned is not original
        assert returned.entries is not original.entries
        # number and title are carried over by value.
        assert returned.number == original.number
        assert returned.title == original.title


def test_filter_by_status_returns_new_entry_objects() -> None:
    """Returned entries are NEW objects; mutating one never touches the input.

    TICKET-034: filter_by_status must return fully independent Entry copies so
    that mutating a returned entry does NOT mutate the original input entry.
    """
    cycles = _filter_fixture()
    original = cycles[0]
    original_first_entry = original.entries[0]
    original_description = original_first_entry.description

    result = filter_by_status(cycles, MergeStatus.MERGED)
    assert result
    returned_entry = result[0].entries[0]

    # The returned entry is a NEW object, not the same object as the input.
    assert returned_entry is not original_first_entry
    # It carries the same field values by value.
    assert returned_entry.description == original_description
    assert returned_entry.status is original_first_entry.status

    # Mutating the returned entry must NOT change the original input entry.
    returned_entry.description = "MUTATED"
    assert original_first_entry.description == original_description
    assert original.entries[0].description == original_description


# ---------------------------------------------------------------------------
# Cycle-header grammar contracts at the render level (TICKET-031, TICKET-032)
# ---------------------------------------------------------------------------


def test_render_out_of_order_cycles_in_file_order() -> None:
    """TICKET-031: render emits cycles in the given (file) order, not sorted."""
    cycles = [
        Cycle(
            number=5,
            title="A",
            entries=[Entry(description="x", status=MergeStatus.MERGED)],
        ),
        Cycle(
            number=3,
            title="B",
            entries=[Entry(description="y", status=MergeStatus.MERGED)],
        ),
    ]
    text = render(cycles)
    lines = text.splitlines()
    # Cycle 5's header appears above cycle 3's header (file order, not sorted).
    assert "## Cycle 5: A" in lines
    assert "## Cycle 3: B" in lines
    assert lines.index("## Cycle 5: A") < lines.index("## Cycle 3: B")


def test_render_leading_zero_re_emitted_normalized() -> None:
    """TICKET-032: a cycle parsed from '## Cycle 007' renders as '## Cycle 7'."""
    from epilogue.parser import parse_log

    cycles = parse_log("## Cycle 007: Build\n- x\n")
    assert cycles[0].number == 7
    text = render(cycles)
    lines = text.splitlines()
    # The normalized header is emitted; the zero-padded form never appears.
    assert "## Cycle 7: Build" in lines
    assert "## Cycle 007: Build" not in lines


def test_render_json_leading_zero_number_is_int() -> None:
    """TICKET-032: render_json emits the normalized base-10 int (7, not '007')."""
    from epilogue.parser import parse_log

    cycles = parse_log("## Cycle 007: Build\n- x\n")
    doc = json.loads(render_json(cycles))
    assert doc["cycles"][0]["number"] == 7
    assert isinstance(doc["cycles"][0]["number"], int)


# ---------------------------------------------------------------------------
# secondary_status in JSON (TICKET-071): optional key, present only when set
# ---------------------------------------------------------------------------


def test_render_json_secondary_status_present_when_set() -> None:
    """A multi-marker entry emits 'secondary_status' with the .value token."""
    cycles = [
        Cycle(
            number=1,
            title="A",
            entries=[
                Entry(
                    description="reverted the no-op",
                    status=MergeStatus.NOT_MERGED,
                    secondary_status=MergeStatus.NO_OP,
                ),
            ],
        ),
    ]
    doc = json.loads(render_json(cycles))
    entry = doc["cycles"][0]["entries"][0]
    assert entry == {
        "description": "reverted the no-op",
        "status": "not_merged",
        "secondary_status": "no_op",
    }


def test_render_json_secondary_status_absent_when_none() -> None:
    """A single-class entry OMITS the 'secondary_status' key (shape unchanged)."""
    cycles = [
        Cycle(
            number=1,
            title="A",
            entries=[
                Entry(description="shipped the feature", status=MergeStatus.MERGED),
                Entry(description="a no-op", status=MergeStatus.NO_OP),
            ],
        ),
    ]
    doc = json.loads(render_json(cycles))
    entries = doc["cycles"][0]["entries"]
    assert entries == [
        {"description": "shipped the feature", "status": "merged"},
        {"description": "a no-op", "status": "no_op"},
    ]
    for entry in entries:
        assert "secondary_status" not in entry


def test_render_json_secondary_status_end_to_end_from_parser() -> None:
    """A multi-marker log line surfaces secondary_status through parse+render."""
    from epilogue.parser import parse_log

    cycles = parse_log("## Cycle 1: A\n- reverted the no-op\n")
    doc = json.loads(render_json(cycles))
    entry = doc["cycles"][0]["entries"][0]
    assert entry["status"] == "not_merged"
    assert entry["secondary_status"] == "no_op"
