# TICKET-047: Hyphenated single-word synonym "un-merged" is not recognized as NOT_MERGED

**Status: CLOSED (Cycle 16).** FIXED: the hyphenated single-word synonym `un-merged` is now recognized as `NOT_MERGED`. Added `("un-merged",)` to `_NOT_MERGED_MARKERS` in `epilogue/parser.py` (a single-token entry, since the tokenizer `_TOKEN_RE=[a-z0-9-]+` treats the hyphen as part of the token), closing the gap with the already-handled `not merged` / `not-merged` / `not-yet-merged` / `not-merged-yet` forms and the verb forms. No bounded-gap matcher or other marker changed. See parser docstring + README "Status inference"; pinned by tests/test_parser.py::test_status_hyphenated_un_merged_recognized, ::test_status_hyphenated_un_merged_plain_merged_regression, ::test_status_hyphenated_un_merged_existing_forms_unchanged. (Cycle 16, PR #19, commit 52c378f.)

## Title
The `NOT_MERGED` marker set recognizes the two-word phrase `not merged`, the
hyphenated compound `not-merged`, the hyphenated compact forms
`not-yet-merged` / `not-merged-yet`, and the verb forms
`reverted`/`reverting`/`reverts`/`abandoned`/`abandoning`/`abandons`, but NOT
the hyphenated single-word synonym `un-merged`. A log author who writes
`un-merged` gets `MERGED` instead of `NOT_MERGED`.

## Evidence
Marker table at `epilogue/parser.py:133-144`:
    _NOT_MERGED_MARKERS: tuple[tuple[str, ...], ...] = (
        ("not", "merged"),
        ("not-merged",),
        ("not-yet-merged",),
        ("not-merged-yet",),
        ("reverted",),
        ("reverting",),
        ("reverts",),
        ("abandoned",),
        ("abandoning",),
        ("abandons",),
    )
There is no `("un-merged",)` entry.

Reproduced against the shipped code (Python 3.10):
    _infer_status("not merged")   # -> not_merged (tokens: ['not','merged'])
    _infer_status("not-merged")   # -> not_merged (tokens: ['not-merged'])
    _infer_status("un-merged")    # -> merged     <-- MISS (tokens: ['un-merged'])

The tokenizer (`epilogue/parser.py:127`) treats a hyphen as part of a token, so
`un-merged` is ONE token, `['un-merged']`, which equals none of the markers and
falls through to the `MERGED` default. `un-merged` is a common hyphenated
spelling of the same concept as `not-merged` (the hyphenated form of the
single-word synonym `unmerged`), yet it is the one hyphenated spelling that
falls through.

## Impact
- A log author who writes `un-merged` (a natural, compact way to say "wasn't
  merged") gets `MERGED` for what is clearly a not-merged change. This is a
  silent truthfulness failure in the mission's core three-way distinction.
- The miss is asymmetric and tied to the hyphenation contract: `not-merged`
  (hyphenated) is recognized, but `un-merged` (hyphenated) is not. A log author
  cannot predict which hyphenated spelling is safe without reading the marker
  table.
- No existing test pins `un-merged`; `tests/test_parser.py` pins `not merged`
  and `not-merged` but never the hyphenated single-word form, so this miss is
  invisible to the gate. (TICKET-042 covers the unhyphenated `unmerged`; this
  ticket covers the hyphenated `un-merged`, a distinct token.)

## Suggestion
Decide the contract and make it true:
- If `un-merged` should be not-merged, add `("un-merged",)` to
  `_NOT_MERGED_MARKERS` (`epilogue/parser.py:133-144`) and update the marker
  enumeration in the module docstring (`epilogue/parser.py:72-76`) and the
  README "Status inference" section.
- If the current set is intentional, document the consequence explicitly
  ("the hyphenated single-word `un-merged` is NOT recognized; only `not
  merged`, `not-merged`, `not-yet-merged`, `not-merged-yet`, and the verb forms
  are") and add a test pinning `_infer_status("un-merged") is
  MergeStatus.MERGED`.
Either way, add a test in `tests/test_parser.py` covering `un-merged` so the
contract is pinned by the gate.
