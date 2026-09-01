# TICKET-049: Hyphenated plural "no-changes" is not recognized as NO_OP

**Status: CLOSED (Cycle 18).** FIXED: the hyphenated plural `no-changes` is now recognized as `NO_OP`. Added `("no-changes",)` to `_NO_OP_MARKERS` in `epilogue/parser.py` (a single-token entry, since the tokenizer `_TOKEN_RE=[a-z0-9-]+` keeps the hyphen inside the token, so `no-changes` is one run), closing the asymmetry with the already-handled `no change` / `no changes` / `no-op` / `no-ops` forms. No other marker or the bounded-gap matcher changed. See parser docstring + README "Status inference"; pinned by tests/test_parser.py::test_status_no_changes_hyphenated_plural_recognized and ::test_status_no_changes_token_boundary_regression. (Cycle 18, PR #21, commit <squash>.)

## Title
The `NO_OP` marker set recognizes the space singular `no change` and the space
plural `no changes`, and the hyphenated `no-op`/`no-ops`, but NOT the hyphenated
plural `no-changes`. A log author who writes `no-changes` gets `MERGED` instead
of `NO_OP`. This is an internal asymmetry: the space plural `no changes` is
recognized, and the hyphenated `no-op`/`no-ops` forms are recognized, but the
hyphenated plural `no-changes` is not.

## Evidence
Marker table at `epilogue/parser.py:145-151`:
    _NO_OP_MARKERS: tuple[tuple[str, ...], ...] = (
        ("no-op",),
        ("no-ops",),
        ("no", "op"),
        ("no", "change"),
        ("no", "changes"),
    )
There is no `("no-changes",)` entry.

Reproduced against the shipped code (Python 3.10):
    _infer_status("no change")    # -> no_op   (tokens: ['no','change'])
    _infer_status("no changes")   # -> no_op   (tokens: ['no','changes'])
    _infer_status("no-changes")   # -> merged  <-- MISS (tokens: ['no-changes'])
    _infer_status("no-ops")       # -> no_op   (tokens: ['no-ops'])

The tokenizer (`epilogue/parser.py:127`) treats a hyphen as part of a token, so
`no-changes` is ONE token, `['no-changes']`, which equals none of the markers
and falls through to the `MERGED` default. The space plural `no changes` IS
recognized, which makes the miss asymmetric: the space plural is honored but the
hyphenated plural is not.

## Impact
- A log author who writes `no-changes` (a natural hyphenated way to say "no
  changes") gets `MERGED` for what is clearly a no-op. This is a silent
  truthfulness failure in the mission's core three-way distinction.
- The miss is asymmetric: the space plural `no changes` is recognized but the
  hyphenated plural `no-changes` is not, even though the hyphenated `no-ops`
  form is. A log author cannot predict which hyphenation is safe without reading
  the marker table.
- No existing test pins `no-changes`; `tests/test_parser.py` pins `no changes`
  (`test_status_morphological_plural_forms_recognized`) and `no-ops` but never
  `no-changes`, so this miss is invisible to the gate. (TICKET-044 covers the
  hyphenated singular `no-change`; this ticket covers the hyphenated plural
  `no-changes`, a distinct token.)

## Suggestion
Decide the contract and make it true:
- If `no-changes` should be a no-op, add `("no-changes",)` to `_NO_OP_MARKERS`
  (`epilogue/parser.py:145-151`) and update the marker enumeration in the module
  docstring (`epilogue/parser.py:75-76`) and the README "Status inference"
  section.
- If the current set is intentional, document the consequence explicitly
  ("the hyphenated plural `no-changes` is NOT recognized; only `no change`,
  `no changes`, `no-op`, `no-ops`, and `no op` are") and add a test pinning
  `_infer_status("no-changes") is MergeStatus.MERGED`.
Either way, add a test in `tests/test_parser.py` covering `no-changes` so the
contract is pinned by the gate.
