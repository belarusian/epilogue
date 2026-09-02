# TICKET-025: Status-inference grammar is documented but not pinned by any test

## Title
The status-inference rule in `epilogue.parser` (marker sets + precedence) is
documented in the module docstring but no test pins the boundary behavior of
`_infer_status`. The existing parser tests only cover the happy markers and one
precedence case; they never assert what happens when a marker word appears as a
substring of an ordinary description, so the defect in TICKET-024 is invisible
to the gate.

## Evidence
`epilogue/parser.py:24-58` documents the exact marker sets and the precedence
`NOT_MERGED > NO_OP > MERGED`. `epilogue/parser.py:63-64` and `80-93` implement
them.

`tests/test_parser.py` covers:
- `test_multi_cycle_all_three_statuses` — happy markers only.
- `test_default_merged_when_no_marker` — a plain description -> MERGED.
- `test_status_precedence_not_merged_over_no_op` — "no-op but reverted" -> NOT_MERGED.
- `test_status_case_insensitive` — "NOT MERGED" / "No-Op" / "No Change".

None of these assert the substring-boundary behavior. In particular there is no
test that pins whether "added a no-op detector" is `no_op` or `merged`, or
whether "shipped the abandoned-cart feature" is `not_merged` or `merged`. The
current (defective) behavior is therefore neither pinned as intended nor as a
known bug — it is simply untested.

## Impact
- The gate (pytest/ruff/mypy) passes with the misclassification from
  TICKET-024 in place, because no test distinguishes the two behaviors.
- A future fix to the marker matching (TICKET-024) has no test to prove it
  changes the right cases and leaves the happy markers intact.
- The documented grammar (docstring) and the tested behavior can drift apart
  with no signal.

## Suggestion
Add tests in `tests/test_parser.py` that pin the boundary behavior, using small
inline logs (no real file):
- A description containing a marker word as a substring of an ordinary phrase
  (e.g. "added a no-op detector", "shipped the abandoned-cart feature") — assert
  the INTENDED status (merged, per the fix in TICKET-024).
- The genuine markers still classify correctly ("no-op: nothing changed" ->
  no_op, "reverted the bad commit" -> not_merged, "abandoned the old approach"
  -> not_merged).
- Precedence and case-insensitivity remain as-is.
These tests should be written to the intended (fixed) behavior so they fail
before TICKET-024's fix lands and pass after.

---
Status: CLOSED (Cycle 8, PR #11, commit db7a42f)
Issue: #58
