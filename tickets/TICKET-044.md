# TICKET-044: Hyphenated singular "no-change" is not recognized as NO_OP

## Title
The `NO_OP` marker set recognizes the space singular `no change` and the space
plural `no changes`, and the hyphenated `no-op`/`no-ops`, but NOT the hyphenated
singular `no-change`. A log author who writes `no-change` gets `MERGED` instead
of `NO_OP`. This is an internal asymmetry: the space singular `no change` is
recognized, but its hyphenated twin `no-change` is not.

## Evidence
Marker table at `epilogue/parser.py:131-136`:
    _NO_OP_MARKERS: tuple[tuple[str, ...], ...] = (
        ("no-op",),
        ("no-ops",),
        ("no", "op"),
        ("no", "change"),
        ("no", "changes"),
    )
There is no `("no-change",)` entry.

Reproduced against the shipped code (Python 3.10):
    _infer_status("no change")   # -> no_op   (tokens: ['no','change'])
    _infer_status("no changes")  # -> no_op   (tokens: ['no','changes'])
    _infer_status("no-change")   # -> merged  <-- MISS (tokens: ['no-change'])
    _infer_status("no-op")       # -> no_op   (tokens: ['no-op'])

The hyphenated singular `no-change` is the one `no change` spelling that falls
through, even though the hyphenated `no-op` form is recognized.

## Impact
- A log author who writes `no-change` (a natural hyphenated way to say "no
  change") gets `MERGED` for what is clearly a no-op. This is a silent
  truthfulness failure in the three-way distinction.
- The miss is asymmetric: the space singular `no change` is recognized but the
  hyphenated singular `no-change` is not, even though the hyphenated `no-op`
  form is. A log author cannot predict which hyphenation is safe without reading
  the marker table.
- No existing test pins `no-change`; `tests/test_parser.py` pins `no change`
  (`test_status_genuine_markers_still_work`) and `no-op`
  (`test_status_no_op_hyphenated_token`) but never `no-change`, so this miss is
  invisible to the gate.

## Suggestion
Decide the contract and make it true:
- If `no-change` should be a no-op, add `("no-change",)` to `_NO_OP_MARKERS`
  (`epilogue/parser.py:131-136`) and update the marker enumeration in the module
  docstring (`epilogue/parser.py:75-76`) and the README "Status inference"
  section.
- If the current set is intentional, document the consequence explicitly
  ("the hyphenated singular `no-change` is NOT recognized; only `no change`,
  `no changes`, `no-op`, `no-ops`, and `no op` are") and add a test pinning
  `_infer_status("no-change") is MergeStatus.MERGED`.
Either way, add a test in `tests/test_parser.py` covering `no-change` so the
contract is pinned by the gate.
Issue: #81
