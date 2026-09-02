# TICKET-056: Undocumented NOT_MERGED markers `not-yet-merged` and `not-merged-yet`

## Title
Two NOT_MERGED markers present in code are missing from every documented marker list.

## Evidence
`epilogue/parser.py` lines 138-139 define two single-token markers:

    _NOT_MERGED_MARKERS: tuple[tuple[str, ...], ...] = (
        ("not", "merged"),
        ("not-merged",),
        ("not-yet-merged",),   # line 138
        ("not-merged-yet",),   # line 139
        ("un-merged",),
        ...
    )

Tests exist for both (`tests/test_parser.py` lines 472-486, referencing TICKET-045).

However, the documented marker list in TWO places omits them:

1. `epilogue/parser.py` module docstring, lines 74-76:

      * ``NOT_MERGED``: ``("not", "merged")``, ``("not-merged",)``,
        ``("un-merged",)``, ``("reverted",)``, ``("reverting",)``,
        ``("reverts",)``, ``("abandoned",)``, ``("abandoning",)``,
        ``("abandons",)``

   `("not-yet-merged",)` and `("not-merged-yet",)` are absent.

2. `README.md`, lines 145-146:

      * `not_merged`: `not merged`, `not-merged`, `un-merged`, `reverted`,
        `reverting`, `reverts`, `abandoned`, `abandoning`, `abandons`

   `not-yet-merged` and `not-merged-yet` are absent.

## Impact
A log author reading the documented marker list cannot predict that
`not-yet-merged` or `not-merged-yet` will classify as `not_merged`. The
README is the primary contract for log authors; an undocumented marker is a
silent behavior that contradicts the documented surface.

## Suggestion
Add `not-yet-merged` and `not-merged-yet` to the NOT_MERGED marker list in
both `epilogue/parser.py` (module docstring, lines 74-76) and `README.md`
(lines 145-146). Also update the "Common morphological variants" sentence to
mention the hyphenated `not-yet-merged` / `not-merged-yet` forms alongside
the existing `not-merged` mention.

**Status: CLOSED (Cycle 22, PR #25).**

Issue: #89
