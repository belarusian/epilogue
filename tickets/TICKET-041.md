# TICKET-041: Imperative/base forms "revert" and "abandon" are not recognized

## Title
The `NOT_MERGED` marker set recognizes the past-tense `reverted` and
`abandoned` and the progressive/plural verb forms `reverting`/`reverts` and
`abandoning`/`abandons`, but NOT the base/imperative forms `revert` and
`abandon`. A log author who writes `revert the change` or `abandon the
renderer` gets `MERGED` instead of `NOT_MERGED`.

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
There is no `("revert",)` and no `("abandon",)` entry.

Reproduced against the shipped code (Python 3.10):
    _infer_status("reverted the change")   # -> not_merged (tokens: ['reverted',...])
    _infer_status("reverting the change")  # -> not_merged
    _infer_status("reverts the change")    # -> not_merged
    _infer_status("revert the change")     # -> merged     <-- MISS
    _infer_status("revert")                # -> merged     <-- MISS
    _infer_status("abandoned the renderer")# -> not_merged
    _infer_status("abandoning the renderer")# -> not_merged
    _infer_status("abandons the renderer") # -> not_merged
    _infer_status("abandon the renderer")  # -> merged     <-- MISS
    _infer_status("abandon")               # -> merged     <-- MISS

The base/imperative form is the one verb form of each stem that is missing,
even though it is a natural way to write a log line ("revert the change",
"abandon the renderer").

## Impact
- A log author who writes the base form `revert`/`abandon` gets `MERGED` for
  what is clearly a not-merged change. This is a silent truthfulness failure in
  the three-way distinction.
- The miss is asymmetric: three of the four verb forms of each stem are
  recognized, but the base form is not. A log author cannot predict which verb
  form is safe without reading the marker table.
- No existing test pins the base forms; `tests/test_parser.py` pins the
  past/progressive/plural forms (`test_status_morphological_verb_forms_recognized`)
  but never `revert` or `abandon`, so this miss is invisible to the gate.

## Suggestion
Decide the contract and make it true:
- If the base forms should be not-merged, add `("revert",)` and `("abandon",)`
  to `_NOT_MERGED_MARKERS` (`epilogue/parser.py:121-129`) and update the marker
  enumeration in the module docstring (`epilogue/parser.py:72-74`) and the
  README "Status inference" section.
- If the current set is intentional, document the consequence explicitly
  ("the base/imperative forms `revert` and `abandon` are NOT recognized; only
  the past, progressive, and plural forms are") and add tests pinning
  `_infer_status("revert") is MergeStatus.MERGED` and
  `_infer_status("abandon") is MergeStatus.MERGED`.
Either way, add tests in `tests/test_parser.py` covering `revert` and `abandon`
so the contract is pinned by the gate.
Issue: #78

Status: CLOSED (Cycle 49, PR #108, merged b99b9d5; Issue: #78). The base/imperative 'abandon' form is now a NOT_MERGED marker via the deliberate contract-A redesign (TICKET-072). 'revert' was already correct (NOT_MERGED) and is unchanged.
