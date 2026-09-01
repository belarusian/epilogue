# TICKET-048: Unseparated plural "noops" is not recognized as NO_OP

**Status: CLOSED (Cycle 17).** FIXED: the unseparated plural `noops` is now recognized as `NO_OP`. Added `("noops",)` to `_NO_OP_MARKERS` in `epilogue/parser.py` (a single-token entry, since the tokenizer `_TOKEN_RE=[a-z0-9-]+` treats `noops` as one run of `[a-z0-9-]`), closing the gap with the already-handled `no-op` / `no-ops` / `no op` / `no operation` / `no operations` / `no change` / `no changes` forms. No other marker or the bounded-gap matcher changed. See parser docstring + README "Status inference"; pinned by tests/test_parser.py::test_status_noops_unseparated_plural_recognized and ::test_status_noops_token_boundary_regression. (Cycle 17, PR #20, commit 1677dac.)

## Title
The `NO_OP` marker set recognizes `no-op` (hyphenated singular), `no-ops`
(hyphenated plural), `no op` (space singular), `no change`, and `no changes`,
but NOT `noops` (the unseparated plural, the plural of the unseparated `noop`).
A log author who writes `noops` gets `MERGED` instead of `NO_OP`.

## Evidence
Marker table at `epilogue/parser.py:145-151`:
    _NO_OP_MARKERS: tuple[tuple[str, ...], ...] = (
        ("no-op",),
        ("no-ops",),
        ("no", "op"),
        ("no", "change"),
        ("no", "changes"),
    )
There is no `("noops",)` entry.

Reproduced against the shipped code (Python 3.10):
    _infer_status("no-op")    # -> no_op   (tokens: ['no-op'])
    _infer_status("no-ops")   # -> no_op   (tokens: ['no-ops'])
    _infer_status("no op")    # -> no_op   (tokens: ['no','op'])
    _infer_status("noops")    # -> merged  <-- MISS (tokens: ['noops'])

The tokenizer (`epilogue/parser.py:127`) splits on whitespace, so `noops` is a
single token, `['noops']`, which equals none of the markers and falls through
to the `MERGED` default. The hyphenated plural `no-ops` IS recognized, which
makes the miss asymmetric: the hyphenated plural is honored but the unseparated
plural is not.

## Impact
- A log author who writes `noops` (a natural, compact plural of "no-op") gets
  `MERGED` for what is clearly a no-op. This is a silent truthfulness failure in
  the mission's core three-way distinction.
- The miss is asymmetric and tied to the marker table: `no-ops` (hyphenated
  plural) is recognized, but `noops` (unseparated plural) is not. A log author
  cannot predict which plural spelling is safe without reading the marker table.
- No existing test pins `noops`; `tests/test_parser.py` pins `no-ops`
  (`test_status_morphological_plural_forms_recognized`) and `no op`
  (`test_status_no_op_space_form`) but never `noops`, so this miss is invisible
  to the gate. (TICKET-043 covers the unseparated singular `noop`; this ticket
  covers the unseparated plural `noops`, a distinct token.)

## Suggestion
Decide the contract and make it true:
- If `noops` should be a no-op, add `("noops",)` to `_NO_OP_MARKERS`
  (`epilogue/parser.py:145-151`) and update the marker enumeration in the module
  docstring (`epilogue/parser.py:75-76`) and the README "Status inference"
  section.
- If the current set is intentional, document the consequence explicitly
  ("the unseparated plural `noops` is NOT recognized; only `no-op`, `no-ops`,
  `no op`, `no change`, and `no changes` are") and add a test pinning
  `_infer_status("noops") is MergeStatus.MERGED`.
Either way, add a test in `tests/test_parser.py` covering `noops` so the
contract is pinned by the gate.
