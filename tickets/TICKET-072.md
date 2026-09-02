# TICKET-072: Deliberate redesign of contract A (cycle 12): imperative abandon/revert forms

## Title
The base/imperative form `abandon` is not a `NOT_MERGED` marker, so a log
author who writes `abandon the renderer` gets `MERGED` for what is clearly a
not-merged change. This is the one remaining verb form of the `abandon` stem
that is missing (past `abandoned`, progressive `abandoning`, plural `abandons`
are all recognized). This ticket is the DELIBERATE, TICKETED redesign of the
pinned Cycle 12 status-inference contract (contract A) that the operator
ruling (2026-09-02) authorized: the pinned clause was a regression baseline,
not an eternal truth, and the constitution's own escape hatch applies.

## Symptom
`_infer_status("abandon the renderer")` and `_infer_status("abandon")` return
`MergeStatus.MERGED`. Every other verb form of the same stem returns
`NOT_MERGED`. The miss is asymmetric and a silent truthfulness failure in the
three-way distinction.

## Evidence
Marker table at `epilogue/parser.py:173-187` (`_NOT_MERGED_MARKERS`):
    ("reverted",), ("reverting",), ("reverts",), ("revert",),
    ("abandoned",), ("abandoning",), ("abandons",),
There is a `("revert",)` entry (line 183) but NO `("abandon",)` entry.

Reproduced against the shipped code (Python 3.10):
    _infer_status("revert the change")     # -> NOT_MERGED  (already correct)
    _infer_status("reverted the change")   # -> NOT_MERGED  (already correct)
    _infer_status("abandoned the renderer")# -> NOT_MERGED
    _infer_status("abandoning the renderer")# -> NOT_MERGED
    _infer_status("abandons the renderer") # -> NOT_MERGED
    _infer_status("abandon the renderer")  # -> MERGED      <-- MISS
    _infer_status("abandon")               # -> MERGED      <-- MISS

### Hypothesis correction (verified against the code)
The briefing's working hypothesis said "revert X / reverted X is a real merged
change and should be recognized as such." That is WRONG. `revert`/`reverted`
ALREADY infer `NOT_MERGED` (line 183 `("revert",)` is present), and that is the
CORRECT status: reverting a change means the change was not kept, so it is a
not-merged change. No parser change is needed for `revert`. The only genuine
defect is the base/imperative `abandon` form. This ticket therefore supersedes
ONLY the `abandon` clause of contract A; the `revert` behavior is untouched and
stays `NOT_MERGED`.

## Proposed minimal additive fix
- Add `("abandon",)` to `_NOT_MERGED_MARKERS` (`epilogue/parser.py:173-187`).
- Update the module docstring marker enumeration (`epilogue/parser.py:98-102`)
  and the contract-A note (`epilogue/parser.py:66-69`) to reflect the amended
  contract.
- Update the README "Status inference" marker list (`README.md:177-179`), the
  contract-A note (`README.md:155-158`), and the non-ASCII example
  (`README.md:231-232`) where `abandoné` is described as `merged`.
- Tests FIRST: add new expectations for the `abandon` base form -> NOT_MERGED
  and `abandoné` -> NOT_MERGED; update the pinned contract-A regression guards
  for EXACTLY the clauses being superseded (each commented
  'contract A redesign per TICKET-072 - was: X, now: Y, because Z'). All
  previously pinned behavior NOT listed here stays green unchanged.

## Supersedes clause
This ticket SUPERSEDES the `abandon` clause of the pinned Cycle 12 contract A
(the clause that documents `abandon` as a non-marker / `MERGED` in the
tokenizer docstring, the README, and the regression guards). It does NOT
supersede the `revert` clause (already `NOT_MERGED`), the `no_op`/`not merged`
phrases, the bounded-gap rule, the token-boundary rule, or the explicit
`[status]` tag mechanism.

## Impact
- A log author who writes the base form `abandon` now gets the truthful
  `NOT_MERGED` status, matching the other three verb forms of the stem.
- The explicit `[status]` tag (TICKET-070) remains the authoritative escape
  hatch and is unaffected.
Issue: #78
Issue: #107

Status: CLOSED (Cycle 49, PR #108, merged b99b9d5; Issue: #107). The abandon clause of contract A was deliberately amended: base/imperative 'abandon' is now a NOT_MERGED marker.
