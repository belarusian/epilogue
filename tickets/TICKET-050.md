# TICKET-050: "nothing changed" is not recognized as NO_OP

**Status: CLOSED (Cycle 19, PR #22).** FIXED: the two-token phrase `nothing changed` is now recognized as `NO_OP`. Added `("nothing", "changed")` to `_NO_OP_MARKERS` in `epilogue/parser.py` (a two-token phrase entry, since the tokenizer `_TOKEN_RE=[a-z0-9-]+` splits `nothing changed` into `['nothing', 'changed']`, so the marker is a phrase -- the same contract as the existing `("no", "operation")` entry), closing the asymmetry with the already-handled `no change` / `no changes` / `no-op` / `no-ops` forms. `nothing to change` is intentionally NOT added this pass (out of scope). No other marker or the bounded-gap matcher changed. See parser docstring + README "Status inference"; pinned by tests/test_parser.py::test_status_nothing_changed_multi_token_recognized and ::test_status_nothing_changed_plain_merged_regression.

## Title
The `NO_OP` marker set recognizes `no-op`/`no-ops`/`no op`, `no change`, and
`no changes`, but NOT the natural phrase `nothing changed`. A log author who
writes `nothing changed` (a common way to record a no-op cycle) gets `MERGED`
instead of `NO_OP`.

## Evidence
Marker table at `epilogue/parser.py:145-151`:
    _NO_OP_MARKERS: tuple[tuple[str, ...], ...] = (
        ("no-op",),
        ("no-ops",),
        ("no", "op"),
        ("no", "change"),
        ("no", "changes"),
    )
There is no `("nothing", "changed")` entry.

Reproduced against the shipped code (Python 3.10):
    _infer_status("no change")     # -> no_op   (tokens: ['no','change'])
    _infer_status("no changes")    # -> no_op   (tokens: ['no','changes'])
    _infer_status("nothing changed")  # -> merged  <-- MISS (tokens: ['nothing','changed'])
    _infer_status("nothing to change")# -> merged  <-- MISS (tokens: ['nothing','to','change'])

The tokenizer (`epilogue/parser.py:127`) splits on whitespace, so `nothing
changed` is TWO tokens, `['nothing', 'changed']`, and `nothing to change` is
THREE tokens, `['nothing', 'to', 'change']`. Neither equals any entry in
`_NO_OP_MARKERS` (the closest, `("no", "change")`, requires the first token to
be `no`, not `nothing`), so both fall through to the `MERGED` default.

## Impact
- A log author who writes `nothing changed` (a natural, unabbreviated way to
  say "no-op") gets `MERGED` for what is clearly a no-op. This is a silent
  truthfulness failure in the mission's core three-way distinction.
- The miss is asymmetric and tied to the marker table: `no change` / `no
  changes` are recognized, but the synonymous `nothing changed` is not. A log
  author cannot predict which phrasing is safe without reading the marker table.
- No existing test pins `nothing changed`; `tests/test_parser.py` pins `no
  change` and `no changes` but never `nothing changed`, so this miss is
  invisible to the gate.

## Suggestion
Decide the contract and make it true:
- If `nothing changed` should be a no-op, add `("nothing", "changed")` (and
  optionally `("nothing", "to", "change")`) to `_NO_OP_MARKERS`
  (`epilogue/parser.py:145-151`) and update the marker enumeration in the module
  docstring (`epilogue/parser.py:75-76`) and the README "Status inference"
  section.
- If the current set is intentional, document the consequence explicitly
  ("the phrase `nothing changed` is NOT recognized; only `no-op`, `no-ops`,
  `no op`, `no change`, and `no changes` are") and add a test pinning
  `_infer_status("nothing changed") is MergeStatus.MERGED`.
Either way, add a test in `tests/test_parser.py` covering `nothing changed` so
the contract is pinned by the gate.

Issue: #83
