# TICKET-036: Morphological variants of markers are not recognized (reverting, no-ops, no changes)

**Status: CLOSED (Cycle 11, PR #15).** FIXED: morphological variants added to the marker tables (reverting/reverts, abandoning/abandons, no-ops, no changes, not-merged). Pinned by tests/test_parser.py::test_status_morphological_verb_forms_recognized, ::test_status_morphological_plural_forms_recognized, ::test_status_hyphenated_compound_not_merged_recognized; token boundaries preserved by ::test_status_morphological_variants_respect_token_boundary. README 'Status inference' updated.

## Title
The status markers are exact, single-form tokens. Common morphological
variants of the same concept — verb forms (`reverting`, `reverts`,
`abandoning`, `abandons`), plurals (`no-ops`, `no changes`), and the
hyphenated compound `not-merged` — are NOT recognized and fall through to
`MERGED`. The capability is documented as "token-based, contiguous-run"
matching, which is correct, but the marker set is so narrow that the most
natural ways a human writes these statuses in a log are missed.

## Evidence
Marker tables at `epilogue/parser.py:101-111`:
    _NOT_MERGED_MARKERS = (("not","merged"), ("reverted",), ("abandoned",))
    _NO_OP_MARKERS      = (("no-op",), ("no","op"), ("no","change"))
Only the exact past-tense / base forms are present.

Reproduced against the shipped code (Python 3.10):
    _infer_status("reverting the change")   # -> merged   (tokens: ['reverting','the','change'])
    _infer_status("reverts the change")     # -> merged   (tokens: ['reverts','the','change'])
    _infer_status("abandoning the renderer")# -> merged   (tokens: ['abandoning','the','renderer'])
    _infer_status("abandons the renderer")  # -> merged   (tokens: ['abandons','the','renderer'])
    _infer_status("no-ops were recorded")   # -> merged   (tokens: ['no-ops','were','recorded'])
    _infer_status("no changes")             # -> merged   (tokens: ['no','changes'])
    _infer_status("not-merged")             # -> merged   (tokens: ['not-merged'])
Contrast the recognized forms:
    _infer_status("reverted the change")    # -> not_merged
    _infer_status("abandoned the renderer") # -> not_merged
    _infer_status("no-op were recorded")    # -> no_op
    _infer_status("no change")              # -> no_op
    _infer_status("not merged")             # -> not_merged

## Impact
- The three-way distinction is the core truthfulness requirement of the
  capability. A log author using the most natural phrasing ("reverting the
  change", "no-ops were recorded", "no changes") gets `MERGED`, so a
  reverted/no-op change is reported as shipped. This is a silent truthfulness
  failure, not a crash.
- The gap is broad: every marker has at least one common variant that is
  missed (verb forms, plurals, hyphenated compounds). The current set covers
  only a narrow slice of how these statuses are actually written.
- No existing test pins the variants; `tests/test_parser.py` only asserts the
  exact forms match, so the miss is invisible to the gate.

## Suggestion
Decide the contract and make it true:
- If variants should be recognized, extend the marker tables to cover the
  common forms (e.g. add `("reverting",)`, `("reverts",)`, `("abandoning",)`,
  `("abandons",)`, `("no-ops",)`, `("no","changes")`, `("not-merged",)`), or
  introduce a small normalization step (stemming/plural-stripping) in
  `_tokenize` (`epilogue/parser.py:126-132`) before matching. Update the
  module docstring's marker list accordingly.
- If exact-form-only is intentional, document it explicitly ("only the exact
  forms listed match; verb forms, plurals, and hyphenated compounds are NOT
  recognized and default to MERGED") and add tests pinning
  `_infer_status("reverting the change") is MergeStatus.MERGED` and
  `_infer_status("no-ops were recorded") is MergeStatus.MERGED`.
Either way, add tests in `tests/test_parser.py` so the contract is pinned.
Issue: #68
