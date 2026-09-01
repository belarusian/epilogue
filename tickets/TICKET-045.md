# TICKET-045: Hyphenated "not-yet-merged" / "not-merged-yet" are not recognized as NOT_MERGED

## Title
The bounded-gap feature (TICKET-038) was added so that the space form
`not yet merged` / `not been merged` classifies as `NOT_MERGED` even with an
intervening word. But the *hyphenated* compact forms `not-yet-merged` and
`not-merged-yet` tokenize to a single token that equals none of the markers,
so they default to `MERGED`. This is an asymmetry: the space form with a gap
is recognized, but its hyphenated twin is not.

## Evidence
Marker table at `epilogue/parser.py:133-142`:
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
The bounded-gap phrase is `("not", "merged")` with
`_NOT_MERGED_PHRASE_MAX_GAP = 2` (`epilogue/parser.py:157-158`), applied in
`_infer_status` at `epilogue/parser.py:246-250`.

Reproduced against the shipped code (Python 3.10):
    _infer_status("not yet merged")    # -> not_merged (tokens: ['not','yet','merged'])
    _infer_status("not been merged")   # -> not_merged (tokens: ['not','been','merged'])
    _infer_status("not-yet-merged")    # -> merged     <-- MISS (tokens: ['not-yet-merged'])
    _infer_status("not-merged-yet")    # -> merged     <-- MISS (tokens: ['not-merged-yet'])

The tokenizer (`epilogue/parser.py:174-180`) treats a hyphen as part of a
token, so `not-yet-merged` is ONE token, not the `("not", "merged")` phrase
with a gap. The bounded-gap matcher never sees two separate tokens.

## Impact
- A log author who writes the compact hyphenated form `not-yet-merged` (a
  natural way to say "wasn't merged yet") gets `MERGED` for what is clearly a
  not-merged change. This is a silent truthfulness failure in the three-way
  distinction.
- The miss is asymmetric and tied to the recently-added bounded-gap feature:
  the space form `not yet merged` is recognized (TICKET-038) but the
  hyphenated `not-yet-merged` is not. A log author cannot predict which
  hyphenation is safe without reading the tokenizer + marker table.
- No existing test pins `not-yet-merged` or `not-merged-yet`;
  `tests/test_parser.py` pins the space forms (`not yet merged`,
  `not been merged`) but never the hyphenated compact forms, so this miss is
  invisible to the gate.

## Suggestion
Decide the contract and make it true:
- If the hyphenated compact forms should be not-merged, add
  `("not-yet-merged",)` and `("not-merged-yet",)` to `_NOT_MERGED_MARKERS`
  (`epilogue/parser.py:133-142`) and update the marker enumeration in the
  module docstring (`epilogue/parser.py:74-76`) and the README "Status
  inference" section.
- If the current set is intentional, document the consequence explicitly
  ("the hyphenated compact forms `not-yet-merged` and `not-merged-yet` are
  NOT recognized; only the space forms `not yet merged` / `not been merged`
  and the contiguous `not merged` / `not-merged` are") and add tests pinning
  `_infer_status("not-yet-merged") is MergeStatus.MERGED` and
  `_infer_status("not-merged-yet") is MergeStatus.MERGED`.
Either way, add tests in `tests/test_parser.py` covering both hyphenated
forms so the contract is pinned by the gate.
