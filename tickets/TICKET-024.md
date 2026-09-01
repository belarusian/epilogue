# TICKET-024: Status inference misclassifies merged work as NO_OP / NOT_MERGED (truthfulness defect)

## Title
The substring-based status inference in `epilogue.parser._infer_status`
mislabels genuinely-merged entries as `no_op` or `not_merged` whenever a
marker word appears as a substring of an ordinary description. This breaks the
mission's core truthfulness requirement ("merges vs no-ops vs NOT MERGED
distinguished truthfully from the log", README line 5).

## Evidence
`epilogue/parser.py:63-64` defines the marker sets:
    _NOT_MERGED_MARKERS = ("not merged", "reverted", "abandoned")
    _NO_OP_MARKERS = ("no-op", "no change")
`epilogue/parser.py:80-93` (`_infer_status`) does a case-insensitive
`marker in lowered` substring test with precedence NOT_MERGED > NO_OP > MERGED.

Reproduced against the shipped parser (Python 3.10, `parse_log`):
    no_op        <- 'added a no-op detector to the pipeline'
    no_op        <- 'verified no change in output'
    not_merged   <- 'documented the reverted behavior'
    not_merged   <- 'shipped the abandoned-cart feature'
Each of these is a real, merged piece of work, yet the parser assigns it a
non-merged status purely because a marker word occurs inside the description.

## Impact
- The three-way distinction is the project's stated core truthfulness
  requirement. A changelog that reports "shipped the abandoned-cart feature"
  under `### Not Merged` is factually wrong.
- The defect propagates to BOTH outputs: the text renderer groups the entry
  under the wrong `###` sub-section (`epilogue/render.py` `_SECTION_ORDER`),
  and `render_json` emits the wrong stable token (`"no_op"` / `"not_merged"`),
  so machine consumers inherit the mislabel.
- The misclassification is silent: the gate (pytest/ruff/mypy) passes because
  no test exercises these descriptions (see TICKET-027).

## Suggestion
Make the markers match as whole words / at a stable position, not as free
substrings. Options (pick one, keep it deterministic and documented):
- Use a word-boundary regex per marker, e.g. `re.search(r"\bno-op\b", lowered)`
  and `re.search(r"\bno change\b", lowered)`, and for NOT_MERGED match the
  phrases as whole phrases (`\bnot merged\b`, `\breverted\b`, `\babandoned\b`)
  so "abandoned-cart" / "reverted behavior" no longer trigger.
- Or require the marker to lead the entry (after the bullet), matching the
  README's own examples (`No-op: ...`, `Abandoned: ...`).
Whichever is chosen, update the module docstring grammar in
`epilogue/parser.py` (lines 24-58) to state the exact rule, and add the four
reproduced descriptions as regression tests (see TICKET-027).
