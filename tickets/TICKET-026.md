# TICKET-026: The NO_OP marker grammar is asymmetric and undocumented in the README

## Title
The `no_op` marker set is `("no-op", "no change")` — it recognizes the
hyphenated "no-op" but NOT the space form "no op", and it treats "no change" as
a free substring. This asymmetry is not documented anywhere a user would look
(the README), so a log author who writes "no op: nothing changed" (a natural
spelling) gets a silently-wrong `merged` classification.

## Evidence
`epilogue/parser.py:64`: `_NO_OP_MARKERS = ("no-op", "no change")`.
`epilogue/parser.py:80-93` does a case-insensitive substring test.

Reproduced against the shipped parser:
    merged       <- 'no op: nothing changed'      (space form: NOT recognized)
    merged       <- 'No Op: nothing changed'      (space form: NOT recognized)
    no_op        <- 'no-op: nothing changed'      (hyphen form: recognized)
    no_op        <- 'there was no change in the API'  (free substring: over-matches)

Two distinct problems in one marker set:
1. "no op" (space) is a common spelling of the same concept but is not matched,
   so it falls through to the MERGED default.
2. "no change" is matched as a substring anywhere, so an ordinary merged
   statement ("there was no change in the API") is mislabeled no_op.

## Impact
- The README (line 5) promises the three statuses are "distinguished
  truthfully", but the README never documents the marker grammar, so a user
  cannot know that "no op" (space) will be misclassified. The truthfulness
  guarantee is only as good as an undocumented, asymmetric rule.
- The over-match on "no change" compounds the TICKET-024 substring defect.
- The asymmetry (hyphen yes, space no) is arbitrary and surprising.

## Suggestion
- Decide and document the canonical marker spellings. If "no op" should count,
  add it (or match `no[- ]op`); if it should not, say so explicitly.
- Constrain "no change" to a whole phrase / leading position (see TICKET-024)
  so ordinary statements are not swallowed.
- Add a short "Status inference" section to the README documenting the exact
  marker set and precedence, so the truthfulness guarantee is backed by a
  documented, user-visible rule.

---
Status: CLOSED (Cycle 8, PR #11, commit db7a42f)
Issue: #60
