# TICKET-040: Space-plural "no ops" is not recognized (asymmetric with "no changes")

## Title
The `NO_OP` marker set recognizes the hyphenated plural `no-ops` and the
space-plural `no changes`, but NOT the space-plural `no ops` (the plural of the
space form `no op`). A log author who writes `no ops` gets `MERGED` instead of
`NO_OP`. This is an internal asymmetry: the space form `no op` is recognized
(`("no","op")`), its hyphenated plural `no-ops` is recognized, and the sibling
space plural `no changes` is recognized — but `no ops` alone is not.

## Evidence
Marker table at `epilogue/parser.py:131-136`:
    _NO_OP_MARKERS: tuple[tuple[str, ...], ...] = (
        ("no-op",),
        ("no-ops",),
        ("no", "op"),
        ("no", "change"),
        ("no", "changes"),
    )
There is no `("no", "ops")` entry.

Reproduced against the shipped code (Python 3.10):
    _infer_status("no op")       # -> no_op    (tokens: ['no','op'])
    _infer_status("no-ops")      # -> no_op    (tokens: ['no-ops'])
    _infer_status("no changes")  # -> no_op    (tokens: ['no','changes'])
    _infer_status("no ops")      # -> merged   (tokens: ['no','ops'])   <-- MISS
    _infer_status("no ops recorded")  # -> merged   (tokens: ['no','ops','recorded'])

The four recognized forms and the one miss are all the same concept ("nothing
changed"), yet the space-plural of `no op` is the single form that falls
through.

## Impact
- A log author who writes `no ops` (a perfectly natural plural of the space
  form `no op`) gets `MERGED` for what is clearly a no-op. This is a silent
  truthfulness failure in the three-way distinction.
- The miss is asymmetric and hard to predict: `no changes` matches but `no ops`
  does not, even though both are space-plurals of recognized space forms. A log
  author cannot tell which plurals are safe without reading the marker table.
- No existing test pins `no ops`; `tests/test_parser.py` pins `no-ops`
  (`test_status_morphological_plural_forms_recognized`) and `no changes` but
  never the space-plural `no ops`, so this miss is invisible to the gate.

## Suggestion
Decide the contract and make it true:
- If `no ops` should be a no-op, add `("no", "ops")` to `_NO_OP_MARKERS`
  (`epilogue/parser.py:131-136`) and update the marker enumeration in the module
  docstring (`epilogue/parser.py:75-76`) and the README "Status inference"
  section.
- If the current set is intentional, document the consequence explicitly
  ("the space-plural `no ops` is NOT recognized; only `no op`, `no-ops`,
  `no change`, and `no changes` are") and add a test pinning
  `_infer_status("no ops") is MergeStatus.MERGED`.
Either way, add a test in `tests/test_parser.py` covering `no ops` so the
contract is pinned by the gate.
Issue: #77
