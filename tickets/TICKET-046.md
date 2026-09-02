# TICKET-046: "no operation" / "no operations" (the full word) are not recognized as NO_OP

**Status: CLOSED (Cycle 15).** FIXED: the full-word expansions `no operation` / `no operations` are now recognized as `NO_OP`. Added `("no", "operation")` and `("no", "operations")` to `_NO_OP_MARKERS` in `epilogue/parser.py` (multi-token entries, since the tokenizer splits on whitespace), closing the gap with the already-handled compact `no-op` / `no-ops` / `no op` / `no change` / `no changes` forms. No NOT_MERGED marker or bounded-gap matcher changed. See parser docstring + README "Status inference"; pinned by tests/test_parser.py::test_status_no_operation_full_word_recognized, ::test_status_no_operations_full_word_recognized, ::test_status_no_operation_compact_form_regression. (Cycle 15, PR #18, commit 328ec72.)

## Title
The `NO_OP` marker set recognizes the compact `no-op` / `no-ops` / `no op`
forms and the `no change` / `no changes` forms, but NOT the full-word
expansion `no operation` / `no operations`. A log author who writes the
unabbreviated `no operation` gets `MERGED` instead of `NO_OP`.

## Evidence
Marker table at `epilogue/parser.py:143-149`:
    _NO_OP_MARKERS: tuple[tuple[str, ...], ...] = (
        ("no-op",),
        ("no-ops",),
        ("no", "op"),
        ("no", "change"),
        ("no", "changes"),
    )
There is no `("no", "operation")` or `("no", "operations")` entry.

Reproduced against the shipped code (Python 3.10):
    _infer_status("no operation")    # -> merged  <-- MISS (tokens: ['no','operation'])
    _infer_status("no operations")   # -> merged  <-- MISS (tokens: ['no','operations'])
    _infer_status("no-op")           # -> no_op
    _infer_status("no op")           # -> no_op
    _infer_status("no change")       # -> no_op

The tokenizer (`epilogue/parser.py:176-180`) splits on whitespace (a token is
a maximal `[a-z0-9-]+` run), so `no operation` is TWO tokens, `['no',
'operation']`, and `no operations` is `['no', 'operations']`. Neither equals
any entry in `_NO_OP_MARKERS`, so both fall through to the `MERGED` default.
The compact `no op` (two tokens `['no','op']`) IS recognized, which makes the
miss asymmetric: the abbreviated form is honored but the unabbreviated one is
not.

## Impact
- A log author who writes the full word `no operation` (a natural,
  unabbreviated way to say "no-op") gets `MERGED` for what is clearly a no-op.
  This is a silent truthfulness failure in the mission's core three-way
  distinction.
- The miss is asymmetric and tied to the marker table: `no op` / `no-op` /
  `no-ops` are recognized, but the full-word `no operation` / `no operations`
  are not. A log author cannot predict which spelling is safe without reading
  the marker table.
- No existing test pins `no operation` or `no operations`;
  `tests/test_parser.py` pins the compact forms (`no-op`, `no op`) but never
  the full-word forms, so this miss is invisible to the gate.

## Suggestion
Decide the contract and make it true:
- If the full-word forms should be no-op (the natural reading), add
  `("no", "operation")` and `("no", "operations")` to `_NO_OP_MARKERS`
  (`epilogue/parser.py:143-149`) and update the marker enumeration in the
  module docstring and the README "Status inference" section.
- If the current set is intentional, document the consequence explicitly
  ("the full-word `no operation` / `no operations` are NOT recognized; only
  the compact `no-op` / `no-ops` / `no op` and `no change` / `no changes`
  are") and add tests pinning
  `_infer_status("no operation") is MergeStatus.MERGED` and
  `_infer_status("no operations") is MergeStatus.MERGED`.
Either way, add tests in `tests/test_parser.py` covering both full-word forms
so the contract is pinned by the gate.
Issue: #72
