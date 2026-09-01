# TICKET-042: Single-word synonym "unmerged" is not recognized as NOT_MERGED

## Title
The `NOT_MERGED` marker set recognizes the two-word phrase `not merged`, the
hyphenated compound `not-merged`, and the verb forms `reverted`/`reverting`/
`reverts`/`abandoned`/`abandoning`/`abandons`, but NOT the single-word synonym
`unmerged`. A log author who writes `unmerged` gets `MERGED` instead of
`NOT_MERGED`.

## Evidence
Marker table at `epilogue/parser.py:121-129`:
    _NOT_MERGED_MARKERS: tuple[tuple[str, ...], ...] = (
        ("not", "merged"),
        ("not-merged",),
        ("reverted",),
        ("reverting",),
        ("reverts",),
        ("abandoned",),
        ("abandoning",),
        ("abandons",),
    )
There is no `("unmerged",)` entry.

Reproduced against the shipped code (Python 3.10):
    _infer_status("not merged")   # -> not_merged (tokens: ['not','merged'])
    _infer_status("not-merged")   # -> not_merged (tokens: ['not-merged'])
    _infer_status("unmerged")     # -> merged     <-- MISS (tokens: ['unmerged'])

`unmerged` is a single, common English word meaning exactly "not merged", yet
it is the one spelling of that concept that falls through to `MERGED`.

## Impact
- A log author who writes `unmerged` (a natural, compact way to say "wasn't
  merged") gets `MERGED` for what is clearly a not-merged change. This is a
  silent truthfulness failure in the three-way distinction.
- The miss is asymmetric: the two-word `not merged` and the hyphenated
  `not-merged` are recognized, but the single-word `unmerged` is not. A log
  author cannot predict which spelling is safe without reading the marker table.
- No existing test pins `unmerged`; `tests/test_parser.py` pins `not merged`
  (`test_status_not_merged_phrase`) and `not-merged`
  (`test_status_hyphenated_compound_not_merged_recognized`) but never `unmerged`,
  so this miss is invisible to the gate.

## Suggestion
Decide the contract and make it true:
- If `unmerged` should be not-merged, add `("unmerged",)` to
  `_NOT_MERGED_MARKERS` (`epilogue/parser.py:121-129`) and update the marker
  enumeration in the module docstring (`epilogue/parser.py:72-74`) and the
  README "Status inference" section.
- If the current set is intentional, document the consequence explicitly
  ("the single-word `unmerged` is NOT recognized; only `not merged`,
  `not-merged`, and the verb forms are") and add a test pinning
  `_infer_status("unmerged") is MergeStatus.MERGED`.
Either way, add a test in `tests/test_parser.py` covering `unmerged` so the
contract is pinned by the gate.
