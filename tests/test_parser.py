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


# ---------------------------------------------------------------------------
# Multi-marker entries preserve the second marker (TICKET-028)
# ---------------------------------------------------------------------------


def test_multi_marker_secondary_status_no_op_preserved() -> None:
    """TICKET-028: a NOT_MERGED + NO_OP entry keeps the second marker.

    The primary status is still NOT_MERGED (precedence unchanged), but the
    NO_OP marker is no longer silently discarded: it is recorded on
    ``secondary_status``.
    """
    log = "## Cycle 1: M\n- reverted the no-op\n"
    entry = parse_log(log)[0].entries[0]
    assert entry.status is MergeStatus.NOT_MERGED
    assert entry.secondary_status is MergeStatus.NO_OP


def test_multi_marker_secondary_status_all_ticket_examples() -> None:
    """TICKET-028: every example from the ticket now surfaces its second marker.

    Each of these carries both a NOT_MERGED and a NO_OP marker; the primary
    stays NOT_MERGED and the discarded NO_OP is now recorded as secondary.
    """
    log = (
        "## Cycle 1: M\n"
        "- reverted the no-op\n"
        "- abandoned the no-op\n"
        "- cleaned up the no-op and the reverted branch\n"
    )
    entries = parse_log(log)[0].entries
    assert [e.status for e in entries] == [
        MergeStatus.NOT_MERGED,
        MergeStatus.NOT_MERGED,
        MergeStatus.NOT_MERGED,
    ]
    assert [e.secondary_status for e in entries] == [
        MergeStatus.NO_OP,
        MergeStatus.NO_OP,
        MergeStatus.NO_OP,
    ]


def test_single_marker_entry_has_no_secondary_status() -> None:
    """TICKET-028: a single-class entry has secondary_status None.

    The common case is unchanged: an entry with only one status class (or
    none) carries no secondary marker.
    """
    log = (
        "## Cycle 1: S\n"
        "- shipped the CLI shell\n"
        "- a no-op: nothing changed\n"
        "- this one was reverted\n"
    )
    entries = parse_log(log)[0].entries
    assert [e.status for e in entries] == [
        MergeStatus.MERGED,
        MergeStatus.NO_OP,
        MergeStatus.NOT_MERGED,
    ]
    assert all(e.secondary_status is None for e in entries)


def test_multi_marker_secondary_status_helper() -> None:
    """TICKET-028: the helper returns (primary, secondary) deterministically."""
    from epilogue.parser import _infer_statuses

    assert _infer_statuses("reverted the no-op") == (
        MergeStatus.NOT_MERGED,
        MergeStatus.NO_OP,
    )
    assert _infer_statuses("no-op but reverted") == (
        MergeStatus.NOT_MERGED,
        MergeStatus.NO_OP,
    )
    assert _infer_statuses("a no-op: nothing changed") == (
        MergeStatus.NO_OP,
        None,
    )
    assert _infer_statuses("shipped the CLI shell") == (
        MergeStatus.MERGED,
        None,
    )


def test_multi_marker_does_not_alter_contract_a_abandon() -> None:
    """TICKET-028 regression guard: the pinned Cycle 12 contract A is unchanged.

    'abandon' is intentionally NOT a marker (it is MERGED), and 'abandoné'
    tokenizes to ['abandon'] and stays MERGED. The multi-marker change must
    not re-open this contract: neither entry gains a NOT_MERGED status or a
    secondary marker.
    """
    log = "## Cycle 1: A\n- abandon the branch\n- abandoné the branch\n"
    entries = parse_log(log)[0].entries
    assert [e.status for e in entries] == [
        MergeStatus.MERGED,
        MergeStatus.MERGED,
    ]
    assert all(e.secondary_status is None for e in entries)


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


def test_status_token_boundary_hyphenated_word_not_merged() -> None:
    """A marker word embedded in a larger hyphenated token does NOT trigger.

    'abandoned-cart' is a single token, so the ('abandoned',) marker does not
    match and the entry classifies as MERGED.
    """
    log = "## Cycle 1: B\n- shipped the abandoned-cart feature\n"
    cycles = parse_log(log)
    assert cycles[0].entries == [
        Entry(description="shipped the abandoned-cart feature", status=MergeStatus.MERGED)
    ]


def test_status_no_op_hyphenated_token() -> None:
    """'no-op' is a single token and matches the ('no-op',) marker -> NO_OP."""
    log = "## Cycle 1: B\n- added a no-op detector\n"
    cycles = parse_log(log)
    assert cycles[0].entries == [
        Entry(description="added a no-op detector", status=MergeStatus.NO_OP)
    ]


def test_status_no_op_space_form() -> None:
    """'no op' (space form) matches the ('no', 'op') marker -> NO_OP."""
    log = "## Cycle 1: B\n- no op: nothing changed\n"
    cycles = parse_log(log)
    assert cycles[0].entries == [
        Entry(description="no op: nothing changed", status=MergeStatus.NO_OP)
    ]


def test_status_reverted_token() -> None:
    """'reverted' as a standalone token matches -> NOT_MERGED."""
    log = "## Cycle 1: B\n- reverted the change\n"
    cycles = parse_log(log)
    assert cycles[0].entries == [
        Entry(description="reverted the change", status=MergeStatus.NOT_MERGED)
    ]


def test_status_not_merged_phrase() -> None:
    """'not merged' as a contiguous token run matches -> NOT_MERGED."""
    log = "## Cycle 1: B\n- not merged yet\n"
    cycles = parse_log(log)
    assert cycles[0].entries == [
        Entry(description="not merged yet", status=MergeStatus.NOT_MERGED)
    ]


def test_status_genuine_markers_still_work() -> None:
    """The genuine markers still classify correctly under token matching."""
    log = (
        "## Cycle 1: B\n"
        "- no-op: nothing changed\n"
        "- abandoned the renderer\n"
        "- no change in output\n"
    )
    cycles = parse_log(log)
    assert cycles[0].entries == [
        Entry(description="no-op: nothing changed", status=MergeStatus.NO_OP),
        Entry(description="abandoned the renderer", status=MergeStatus.NOT_MERGED),
        Entry(description="no change in output", status=MergeStatus.NO_OP),
    ]


# ---------------------------------------------------------------------------
# Cycle-header grammar contracts (TICKET-030..033)
# ---------------------------------------------------------------------------


def test_duplicate_numbers_kept_in_file_order() -> None:
    """TICKET-030: two headers with the SAME number keep BOTH, in file order."""
    log = (
        "## Cycle 2: A\n"
        "- x\n"
        "## Cycle 2: B\n"
        "- y\n"
    )
    cycles = parse_log(log)
    assert len(cycles) == 2
    assert [c.number for c in cycles] == [2, 2]
    assert [c.title for c in cycles] == ["A", "B"]
    # Each cycle keeps its own entries, in file order.
    assert cycles[0].entries == [
        Entry(description="x", status=MergeStatus.MERGED)
    ]
    assert cycles[1].entries == [
        Entry(description="y", status=MergeStatus.MERGED)
    ]


def test_out_of_order_numbers_kept_in_file_order_not_sorted() -> None:
    """TICKET-031: cycles are returned in FILE ORDER, never sorted by number."""
    log = (
        "## Cycle 5: A\n"
        "- x\n"
        "## Cycle 3: B\n"
        "- y\n"
    )
    cycles = parse_log(log)
    assert len(cycles) == 2
    # File order (5 then 3), NOT sorted ascending (3 then 5).
    assert [c.number for c in cycles] == [5, 3]
    assert [c.title for c in cycles] == ["A", "B"]


def test_leading_zero_number_normalized_to_int() -> None:
    """TICKET-032: the number is a base-10 int, so leading zeros are dropped."""
    cycles = parse_log("## Cycle 007: Build\n- x\n")
    assert len(cycles) == 1
    assert cycles[0].number == 7
    assert isinstance(cycles[0].number, int)
    assert cycles[0].title == "Build"


def test_indented_header_yields_no_cycle() -> None:
    """TICKET-033: an indented header (spaces or tab) is NOT a header."""
    # Leading spaces.
    assert parse_log("  ## Cycle 2: Build\n- x\n") == []
    # Leading tab.
    assert parse_log("\t## Cycle 2: Build\n- x\n") == []
    # Mixed leading whitespace.
    assert parse_log(" \t ## Cycle 2: Build\n- x\n") == []


def test_internal_whitespace_is_lenient() -> None:
    """TICKET-033: tabs, multiple spaces, and spaces around the colon parse."""
    cases = [
        "##\tCycle 2: Build",   # tab between ## and Cycle
        "##  Cycle 2: Build",    # multiple spaces between ## and Cycle
        "## Cycle 2 : Build",    # space before the colon
        "## Cycle 2:Build",      # no space after the colon
    ]
    for header in cases:
        cycles = parse_log(header + "\n- x\n")
        assert len(cycles) == 1, f"header {header!r} should parse"
        assert cycles[0].number == 2
        assert cycles[0].title == "Build"


# ---------------------------------------------------------------------------
# Status-inference tokenizer contract (TICKET-036/037/039; TICKET-035 subsumed)
# ---------------------------------------------------------------------------


def test_status_morphological_verb_forms_recognized() -> None:
    """TICKET-036: verb forms reverting/reverts/abandoning/abandons match.

    These fell through to MERGED before the marker expansion; each must now
    classify NOT_MERGED.
    """
    log = (
        "## Cycle 1: V\n"
        "- reverting the change\n"
        "- reverts the change\n"
        "- abandoning the renderer\n"
        "- abandons the renderer\n"
    )
    cycles = parse_log(log)
    assert [e.status for e in cycles[0].entries] == [
        MergeStatus.NOT_MERGED,
        MergeStatus.NOT_MERGED,
        MergeStatus.NOT_MERGED,
        MergeStatus.NOT_MERGED,
    ]


def test_status_morphological_plural_forms_recognized() -> None:
    """TICKET-036: plurals no-ops / no changes match the NO_OP markers."""
    log = (
        "## Cycle 1: P\n"
        "- no-ops were recorded\n"
        "- no changes in output\n"
    )
    cycles = parse_log(log)
    assert [e.status for e in cycles[0].entries] == [
        MergeStatus.NO_OP,
        MergeStatus.NO_OP,
    ]


def test_status_hyphenated_compound_not_merged_recognized() -> None:
    """TICKET-036: the hyphenated compound 'not-merged' is a single token and
    now matches the NOT_MERGED marker (it fell through to MERGED before)."""
    log = "## Cycle 1: C\n- not-merged\n"
    cycles = parse_log(log)
    assert cycles[0].entries[0].status is MergeStatus.NOT_MERGED


def test_status_morphological_variants_respect_token_boundary() -> None:
    """Regression guard: adding verb/plural forms must NOT loosen token
    boundaries. A variant stem embedded in a larger word (reversion,
    abandonment, abandoning-cart) is one token and stays MERGED."""
    log = (
        "## Cycle 1: B\n"
        "- the reversion was clean\n"
        "- abandonment of the branch\n"
        "- shipped the abandoning-cart feature\n"
    )
    cycles = parse_log(log)
    assert [e.status for e in cycles[0].entries] == [
        MergeStatus.MERGED,
        MergeStatus.MERGED,
        MergeStatus.MERGED,
    ]


def test_status_marker_glued_to_hyphen_or_digit_defaults_merged() -> None:
    """TICKET-039 (subsumes TICKET-035): a correctly spelled marker glued to a
    hyphen or digit on either side is ONE token that equals no marker, so it
    defaults to MERGED. This is a pinned contract, not a bug to fix silently.

    Punctuation such as ':' or '.' IS a separator, so the clean/punctuated
    forms still match (asserted to pin the asymmetry)."""
    from epilogue.parser import _infer_status

    # Glued to a hyphen or digit -> one token -> MERGED.
    for glued in ("no-op-", "-no-op", "no--op", "no-op2", "reverted2", "abandoned-"):
        assert _infer_status(glued) is MergeStatus.MERGED, glued
    # Punctuation is a separator -> the marker still matches.
    assert _infer_status("no-op: nothing changed") is MergeStatus.NO_OP
    assert _infer_status("reverted.") is MergeStatus.NOT_MERGED


def test_status_non_ascii_dropped_not_folded() -> None:
    r"""TICKET-037: non-ASCII characters are dropped (not transliterated), so a
    marker matches only when its ASCII stem survives tokenizing. The SAME
    trailing character yields different statuses depending on the stem — a
    pinned contract.

    'revertedé' -> ['reverted'] (marker) -> NOT_MERGED;
    'no-opé'    -> ['no-op']    (marker) -> NO_OP;
    'abandoné'   -> ['abandon']  (no marker) -> MERGED.
    """
    from epilogue.parser import _infer_status, _tokenize

    assert _tokenize("revertedé") == ["reverted"]
    assert _tokenize("abandoné") == ["abandon"]
    assert _infer_status("revertedé") is MergeStatus.NOT_MERGED
    assert _infer_status("no-opé") is MergeStatus.NO_OP
    assert _infer_status("abandoné") is MergeStatus.MERGED


# ---------------------------------------------------------------------------
# Bounded-gap rule for the ("not", "merged") phrase (TICKET-038, contract A)
# ---------------------------------------------------------------------------


def test_status_not_merged_phrase_with_intervening_word() -> None:
    """TICKET-038: a single intervening word between 'not' and 'merged' still
    matches the NOT_MERGED phrase (bounded gap of up to two tokens).

    'not yet merged' and 'not been merged' are the most natural ways to write
    "wasn't merged"; both must classify NOT_MERGED (they fell through to
    MERGED under the strict contiguous-run rule).
    """
    log = (
        "## Cycle 1: G\n"
        "- not yet merged\n"
        "- not been merged\n"
    )
    cycles = parse_log(log)
    assert [e.status for e in cycles[0].entries] == [
        MergeStatus.NOT_MERGED,
        MergeStatus.NOT_MERGED,
    ]


def test_status_not_merged_phrase_with_leading_word_and_intervening_word() -> None:
    """TICKET-038: words before the phrase and one intervening word are fine.

    'has not been merged' -> ['has','not','been','merged']; 'not' and 'merged'
    have one intervening token ('been'), so it matches NOT_MERGED.
    """
    log = "## Cycle 1: G\n- has not been merged\n"
    cycles = parse_log(log)
    assert cycles[0].entries == [
        Entry(description="has not been merged", status=MergeStatus.NOT_MERGED)
    ]


def test_status_not_merged_phrase_with_two_intervening_words() -> None:
    """TICKET-038: two intervening words is the maximum allowed gap.

    'not yet been merged' -> ['not','yet','been','merged']; 'not' and 'merged'
    have two intervening tokens, which is exactly _NOT_MERGED_PHRASE_MAX_GAP,
    so it still matches NOT_MERGED.
    """
    log = "## Cycle 1: G\n- not yet been merged\n"
    cycles = parse_log(log)
    assert cycles[0].entries == [
        Entry(description="not yet been merged", status=MergeStatus.NOT_MERGED)
    ]


def test_status_not_merged_phrase_large_gap_defaults_merged() -> None:
    """TICKET-038 regression guard: a gap of 3+ intervening tokens does NOT
    match the phrase, so the entry defaults to MERGED.

    'not a b c merged' -> ['not','a','b','c','merged']; 'not' and 'merged'
    have three intervening tokens (a, b, c), which exceeds the max gap of two,
    so the phrase does not match and the entry is MERGED.
    """
    log = "## Cycle 1: G\n- not a b c merged\n"
    cycles = parse_log(log)
    assert cycles[0].entries == [
        Entry(description="not a b c merged", status=MergeStatus.MERGED)
    ]


def test_bounded_gap_run_helper_contract() -> None:
    """TICKET-038: pin the _has_bounded_gap_run helper's contract directly.

    - max_gap == 0 is identical to _has_contiguous_run.
    - a marker longer than the token list never matches.
    - a gap of exactly max_gap intervening tokens matches; max_gap + 1 does not.
    """
    from epilogue.parser import (
        _has_bounded_gap_run,
        _has_contiguous_run,
    )

    # max_gap == 0 is identical to the contiguous-run helper.
    for tokens in (
        ["not", "merged"],
        ["not", "yet", "merged"],
        ["not", "a", "b", "c", "merged"],
        ["merged", "not"],
    ):
        assert _has_bounded_gap_run(tokens, ("not", "merged"), 0) == (
            _has_contiguous_run(tokens, ("not", "merged"))
        ), tokens

    # A marker longer than the token list never matches.
    assert _has_bounded_gap_run(["not"], ("not", "merged"), 2) is False
    assert _has_bounded_gap_run([], ("not", "merged"), 2) is False

    # Exactly max_gap intervening tokens matches; max_gap + 1 does not.
    assert _has_bounded_gap_run(["not", "a", "b", "merged"], ("not", "merged"), 2) is True
    assert _has_bounded_gap_run(["not", "a", "b", "c", "merged"], ("not", "merged"), 2) is False


def test_status_hyphenated_not_yet_merged_recognized() -> None:
    """TICKET-045: the compact hyphenated form 'not-yet-merged' is a single
    token and must classify NOT_MERGED (it fell through to MERGED before)."""
    log = "## Cycle 1: H\n- not-yet-merged\n"
    cycles = parse_log(log)
    assert cycles[0].entries[0].status is MergeStatus.NOT_MERGED


def test_status_hyphenated_not_merged_yet_recognized() -> None:
    """TICKET-045: the compact hyphenated form 'not-merged-yet' is a single
    token and must classify NOT_MERGED (it fell through to MERGED before)."""
    log = "## Cycle 1: H\n- not-merged-yet\n"
    cycles = parse_log(log)
    assert cycles[0].entries[0].status is MergeStatus.NOT_MERGED


def test_status_hyphenated_not_merged_space_form_regression() -> None:
    """TICKET-045 regression guard: the space form 'not yet merged' (TICKET-038)
    and the plain 'merged' line must keep their statuses after adding the
    hyphenated markers (no over-match)."""
    log = (
        "## Cycle 1: H\n"
        "- not yet merged\n"
        "- merged\n"
    )
    cycles = parse_log(log)
    assert [e.status for e in cycles[0].entries] == [
        MergeStatus.NOT_MERGED,
        MergeStatus.MERGED,
    ]


def test_status_no_operation_full_word_recognized() -> None:
    """TICKET-046: the full-word 'no operation' must classify as NO_OP (not
    the MERGED default)."""
    log = (
        "## Cycle 1: H\n"
        "- no operation\n"
    )
    cycles = parse_log(log)
    assert [e.status for e in cycles[0].entries] == [MergeStatus.NO_OP]


def test_status_no_operations_full_word_recognized() -> None:
    """TICKET-046: the full-word plural 'no operations' must classify as NO_OP
    (not the MERGED default)."""
    log = (
        "## Cycle 1: H\n"
        "- no operations\n"
    )
    cycles = parse_log(log)
    assert [e.status for e in cycles[0].entries] == [MergeStatus.NO_OP]


def test_status_no_operation_compact_form_regression() -> None:
    """TICKET-046 regression guard: the compact 'no-op' (TICKET-011/026) must
    stay NO_OP and a plain 'merged' line must stay MERGED after adding the
    full-word markers (no over-match)."""
    log = (
        "## Cycle 1: H\n"
        "- no-op\n"
        "- merged\n"
    )
    cycles = parse_log(log)
    assert [e.status for e in cycles[0].entries] == [
        MergeStatus.NO_OP,
        MergeStatus.MERGED,
    ]


# ---------------------------------------------------------------------------
# Hyphenated single-word synonym "un-merged" (TICKET-047)
# ---------------------------------------------------------------------------


def test_status_hyphenated_un_merged_recognized() -> None:
    """TICKET-047 fix-pin: the hyphenated single-word synonym 'un-merged' is a
    single token (the tokenizer treats the hyphen as part of the token) and
    must classify NOT_MERGED (it fell through to MERGED before)."""
    from epilogue.parser import _infer_status, _tokenize

    assert _tokenize("un-merged") == ["un-merged"]
    assert _infer_status("un-merged") is MergeStatus.NOT_MERGED


def test_status_hyphenated_un_merged_plain_merged_regression() -> None:
    """TICKET-047 regression guard: adding the 'un-merged' marker must NOT
    over-match. A plain 'merged' line stays MERGED (no marker, default)."""
    from epilogue.parser import _infer_status

    assert _infer_status("merged") is MergeStatus.MERGED


def test_status_hyphenated_un_merged_existing_forms_unchanged() -> None:
    """TICKET-047: the existing NOT_MERGED forms are unchanged after adding
    'un-merged'. The hyphenated compound 'not-merged' (single token) and the
    two-word phrase 'not merged' both still classify NOT_MERGED."""
    from epilogue.parser import _infer_status

    assert _infer_status("not-merged") is MergeStatus.NOT_MERGED
    assert _infer_status("not merged") is MergeStatus.NOT_MERGED


# ---------------------------------------------------------------------------
# Unseparated plural "noops" (TICKET-048)
# ---------------------------------------------------------------------------


def test_status_noops_unseparated_plural_recognized() -> None:
    """TICKET-048 fix-pin: the unseparated plural 'noops' is a single token
    (the tokenizer treats it as one run of [a-z0-9-]) and must classify NO_OP
    (it fell through to the MERGED default before)."""
    log = (
        "## Cycle 1: N\n"
        "- noops were recorded\n"
    )
    cycles = parse_log(log)
    assert [e.status for e in cycles[0].entries] == [MergeStatus.NO_OP]


def test_status_noops_token_boundary_regression() -> None:
    """TICKET-048 regression guard: adding the 'noops' marker must NOT loosen
    token boundaries. 'noops' embedded in a larger hyphenated token is one
    token that equals no marker and stays MERGED, and a plain 'merged' line
    stays MERGED (no over-match)."""
    from epilogue.parser import _infer_status, _tokenize

    assert _tokenize("noops") == ["noops"]
    assert _infer_status("noops") is MergeStatus.NO_OP
    assert _infer_status("the noops-detector shipped") is MergeStatus.MERGED
    assert _infer_status("merged") is MergeStatus.MERGED


# ---------------------------------------------------------------------------
# Hyphenated plural "no-changes" (TICKET-049)
# ---------------------------------------------------------------------------


def test_status_no_changes_hyphenated_plural_recognized() -> None:
    """TICKET-049 fix-pin: the hyphenated plural 'no-changes' is a single
    token (the tokenizer keeps the hyphen inside the token) and must classify
    NO_OP (it fell through to the MERGED default before)."""
    log = (
        "## Cycle 1: N\n"
        "- no-changes were recorded\n"
    )
    cycles = parse_log(log)
    assert [e.status for e in cycles[0].entries] == [MergeStatus.NO_OP]


def test_status_no_changes_token_boundary_regression() -> None:
    """TICKET-049 regression guard: adding the 'no-changes' marker must NOT
    loosen token boundaries. 'no-changes' embedded in a larger hyphenated
    token is one token that equals no marker and stays MERGED, and a plain
    'merged' line stays MERGED (no over-match)."""
    from epilogue.parser import _infer_status, _tokenize

    assert _tokenize("no-changes") == ["no-changes"]
    assert _infer_status("no-changes") is MergeStatus.NO_OP
    assert _infer_status("the no-changes-detector shipped") is MergeStatus.MERGED
    assert _infer_status("merged") is MergeStatus.MERGED


# ---------------------------------------------------------------------------
# Multi-token phrase "nothing changed" (TICKET-050)
# ---------------------------------------------------------------------------


def test_status_nothing_changed_multi_token_recognized() -> None:
    """TICKET-050: the two-token phrase 'nothing changed' must classify as
    NO_OP (not the MERGED default). The tokenizer splits it into
    ['nothing', 'changed'], so the marker is a two-token phrase -- the same
    contract as the existing ('no', 'operation') entry."""
    log = (
        "## Cycle 1: H\n"
        "- nothing changed\n"
    )
    cycles = parse_log(log)
    assert [e.status for e in cycles[0].entries] == [MergeStatus.NO_OP]


def test_status_nothing_changed_plain_merged_regression() -> None:
    """TICKET-050 regression guard: adding the 'nothing changed' marker must
    NOT over-match. A plain 'merged' line stays MERGED (no marker, default)."""
    log = (
        "## Cycle 1: H\n"
        "- nothing changed\n"
        "- merged\n"
    )
    cycles = parse_log(log)
    assert [e.status for e in cycles[0].entries] == [
        MergeStatus.NO_OP,
        MergeStatus.MERGED,
    ]


# ---------------------------------------------------------------------------
# Documentation consistency (TICKET-056)
# ---------------------------------------------------------------------------


def test_not_merged_markers_documented_in_readme_and_docstring() -> None:
    """TICKET-056: every single-token NOT_MERGED marker in the code must be
    present in BOTH the README.md not_merged list AND the parser module
    docstring NOT_MERGED list. This reproduces the defect (fails before the
    doc fix because not-yet-merged/not-merged-yet were absent from the docs)
    and pins it (passes after)."""
    from pathlib import Path

    import epilogue.parser as parser_mod

    # Extract single-token markers from the actual code table.
    single_token_markers = [m[0] for m in parser_mod._NOT_MERGED_MARKERS if len(m) == 1]
    assert single_token_markers, "expected at least one single-token NOT_MERGED marker"

    # Read README.md from the repo root (relative to this test file).
    repo_root = Path(__file__).resolve().parent.parent
    readme_text = (repo_root / "README.md").read_text(encoding="utf-8")

    # Extract the not_merged list block from README.
    # It starts at the line containing '* `not_merged`:' and continues until
    # the next bullet or blank line.
    readme_lines = readme_text.splitlines()
    readme_block_lines: list[str] = []
    in_block = False
    for line in readme_lines:
        if "* `not_merged`:" in line:
            in_block = True
            readme_block_lines.append(line)
            continue
        if in_block:
            if line.strip() == "" or line.lstrip().startswith("* "):
                break
            readme_block_lines.append(line)
    readme_block = "\n".join(readme_block_lines)

    # Read the parser module docstring.
    docstring = parser_mod.__doc__ or ""
    doc_lines = docstring.splitlines()
    doc_block_lines: list[str] = []
    in_block = False
    for line in doc_lines:
        if "``NOT_MERGED``:" in line:
            in_block = True
            doc_block_lines.append(line)
            continue
        if in_block:
            if line.strip() == "" or line.lstrip().startswith("* "):
                break
            doc_block_lines.append(line)
    doc_block = "\n".join(doc_block_lines)

    # Assert each single-token marker appears in both documented lists.
    for marker in single_token_markers:
        assert marker in readme_block, (
            f"single-token NOT_MERGED marker {marker!r} is missing from the "
            f"README.md not_merged list"
        )
        assert marker in doc_block, (
            f"single-token NOT_MERGED marker {marker!r} is missing from the "
            f"parser module docstring NOT_MERGED list"
        )


# ---------------------------------------------------------------------------
# Cycle 46: marker-table additions (TICKET-040..044)
# ---------------------------------------------------------------------------


def test_status_no_change_hyphenated_singular_recognized() -> None:
    """TICKET-044 fix-pin: the hyphenated singular 'no-change' is a single
    token and must classify NO_OP (it fell through to the MERGED default before)."""
    log = (
        "## Cycle 1: N\n"
        "- no-change was recorded\n"
    )
    cycles = parse_log(log)
    assert [e.status for e in cycles[0].entries] == [MergeStatus.NO_OP]


def test_status_noop_unseparated_singular_recognized() -> None:
    """TICKET-043 fix-pin: the unseparated singular 'noop' is a single token
    and must classify NO_OP (it fell through to the MERGED default before)."""
    log = (
        "## Cycle 1: N\n"
        "- noop was recorded\n"
    )
    cycles = parse_log(log)
    assert [e.status for e in cycles[0].entries] == [MergeStatus.NO_OP]


def test_status_no_ops_space_plural_recognized() -> None:
    """TICKET-040 fix-pin: the space-plural 'no ops' (two tokens) must classify
    NO_OP, symmetric with the existing 'no changes' entry."""
    log = (
        "## Cycle 1: N\n"
        "- no ops were recorded\n"
    )
    cycles = parse_log(log)
    assert [e.status for e in cycles[0].entries] == [MergeStatus.NO_OP]


def test_status_unmerged_single_word_recognized() -> None:
    """TICKET-042 fix-pin: the single-word 'unmerged' (no hyphen) is a single
    token and must classify NOT_MERGED (it fell through to the MERGED default before)."""
    log = (
        "## Cycle 1: B\n"
        "- unmerged the branch\n"
    )
    cycles = parse_log(log)
    assert [e.status for e in cycles[0].entries] == [MergeStatus.NOT_MERGED]


def test_status_revert_base_form_recognized() -> None:
    """TICKET-041 fix-pin (partial): the base/imperative form 'revert' is a
    single token and must classify NOT_MERGED. Note: 'abandon' is intentionally
    NOT added because the pinned Cycle 12 contract (contract A) documents
    'abandon' as a non-marker (MERGED) in the tokenizer docstring and a
    regression test pins that behavior."""
    log = (
        "## Cycle 1: B\n"
        "- revert the change\n"
    )
    cycles = parse_log(log)
    assert [e.status for e in cycles[0].entries] == [MergeStatus.NOT_MERGED]
