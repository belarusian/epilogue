# TICKET-028: Status precedence silently discards the second marker in multi-marker entries

## Title
When a single entry's description contains more than one status marker, the
fixed precedence `NOT_MERGED > NO_OP > MERGED` picks the first match and
silently discards the rest. This is deterministic but not documented as a
lossy rule, and it mislabels entries that legitimately mention a marker word
while describing different work.

## Evidence
`epilogue/parser.py:80-93` (`_infer_status`) returns on the first marker found,
scanning NOT_MERGED markers before NO_OP markers before defaulting to MERGED.
The docstring (lines 30-33) states the precedence but not that it is lossy.

Reproduced against the shipped parser:
    not_merged   <- 'reverted the no-op'
    not_merged   <- 'abandoned the no-op'
    not_merged   <- 'cleaned up the no-op and the reverted branch'

The third line describes a merged cleanup task that merely *mentions* both a
no-op and a reverted branch, yet it is classified `not_merged` because the
NOT_MERGED scan hits "reverted" first. The NO_OP marker is never even
considered.

## Impact
- The precedence rule turns a multi-marker description into a single status
  with no signal that information was dropped. A reader of the changelog (or a
  machine consumer of the JSON token) cannot tell that the entry also carried a
  no-op marker.
- Combined with the substring matching (TICKET-024), the precedence makes
  misclassification more likely, not less: any incidental mention of a
  NOT_MERGED word forces NOT_MERGED regardless of the entry's real status.
- The rule is deterministic (good) but undocumented as lossy (bad), so the
  behavior is surprising.

## Suggestion
- Document the precedence explicitly as a lossy, first-match rule in the module
  docstring and the README, OR
- Change the rule to be less lossy: e.g. require the *leading* marker (after
  the bullet) to decide, so incidental mentions later in the line do not
  dominate; or
- Add an explicit status tag (TICKET-027) so multi-marker entries can be
  disambiguated at the source.
Add a test pinning the chosen behavior for a multi-marker entry.
