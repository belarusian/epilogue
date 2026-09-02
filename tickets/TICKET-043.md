# TICKET-043: "noop" (no separator) is not recognized as NO_OP

## Title
The `NO_OP` marker set recognizes `no-op` (hyphenated), `no-ops` (hyphenated
plural), `no op` (space), `no change`, and `no changes`, but NOT `noop` (the
two letters with no separator at all). A log author who writes `noop` gets
`MERGED` instead of `NO_OP`.

## Evidence
Marker table at `epilogue/parser.py:131-136`:
    _NO_OP_MARKERS: tuple[tuple[str, ...], ...] = (
        ("no-op",),
        ("no-ops",),
        ("no", "op"),
        ("no", "change"),
        ("no", "changes"),
    )
There is no `("noop",)` entry.

Reproduced against the shipped code (Python 3.10):
    _infer_status("no-op")    # -> no_op   (tokens: ['no-op'])
    _infer_status("no op")    # -> no_op   (tokens: ['no','op'])
    _infer_status("noop")     # -> merged  <-- MISS (tokens: ['noop'])

`noop` is a common compact spelling of "no-op" (the same way `not` is written
without a space in `not-merged`), yet it is the one spelling that falls through
to `MERGED`.

## Impact
- A log author who writes `noop` (a natural, compact way to say "no-op") gets
  `MERGED` for what is clearly a no-op. This is a silent truthfulness failure in
  the three-way distinction.
- The miss is asymmetric: the hyphenated `no-op` and the space form `no op` are
  recognized, but the unseparated `noop` is not. A log author cannot predict
  which spelling is safe without reading the marker table.
- No existing test pins `noop`; `tests/test_parser.py` pins `no-op`
  (`test_status_no_op_hyphenated_token`) and `no op`
  (`test_status_no_op_space_form`) but never `noop`, so this miss is invisible
  to the gate.

## Suggestion
Decide the contract and make it true:
- If `noop` should be a no-op, add `("noop",)` to `_NO_OP_MARKERS`
  (`epilogue/parser.py:131-136`) and update the marker enumeration in the module
  docstring (`epilogue/parser.py:75-76`) and the README "Status inference"
  section.
- If the current set is intentional, document the consequence explicitly
  ("the unseparated `noop` is NOT recognized; only `no-op`, `no-ops`, `no op`,
  `no change`, and `no changes` are") and add a test pinning
  `_infer_status("noop") is MergeStatus.MERGED`.
Either way, add a test in `tests/test_parser.py` covering `noop` so the
contract is pinned by the gate.
Issue: #80
