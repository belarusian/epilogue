# TICKET-060: Bounded-gap mechanism is a blunt instrument - matches any 2 intervening tokens, not just adverbs
**Status: CLOSED (Cycle 25) — documented design constraint, not a defect.** This ticket is the meta-analysis of 057 + 058: `_has_bounded_gap_run` is a pure distance check, and that is the documented, deliberate design. `README.md` (lines 161-167) and the parser docstring (lines 93-100) describe the rule as a token-distance cap (`_NOT_MERGED_PHRASE_MAX_GAP`), not a linguistic classifier; the deterministic token-based approach was chosen in Cycle 12 (TICKET-038, 'contract A') precisely so the rule stays predictable and testable. The ticket's Option 3 ('document the exact contract') is already satisfied by that documentation. Options 1-2 replace the distance check with a content-aware classifier — a redesign of the status-inference contract that breaks `::test_bounded_gap_run_helper_contract`. Superseded by the documented design; no code change.

## Title
The `_has_bounded_gap_run` helper for `("not", "merged")` allows *any* two
intervening tokens, not just the adverbs (`yet`, `been`) that motivated the
feature. This causes both false positives (TICKET-058) and false negatives
(TICKET-057) and makes the behavior hard to predict for log authors.

## Evidence
`epilogue/parser.py` lines 205-239 (`_has_bounded_gap_run`):

    def _has_bounded_gap_run(tokens, marker, max_gap):
        ...
        reachable = {i for i, tok in enumerate(tokens) if tok == marker[0]}
        for pos in range(1, marker_len):
            next_reachable = set()
            for j, tok in enumerate(tokens):
                if tok != marker[pos]:
                    continue
                if any(j - max_gap - 1 <= i <= j - 1 for i in reachable):
                    next_reachable.add(j)
            ...

The helper checks only the *distance* between `not` and `merged` (<= 2
intervening tokens). It does not inspect the *content* of the intervening
tokens. The module docstring (lines 90-97) says the gap exists for "natural
phrasings of 'wasn't merged'" that "insert a word between `not` and
`merged` (`yet`, `been`)", but the implementation accepts any two tokens:

| Intervening tokens | Example | Result | Intended? |
|---|---|---|---|
| `yet` | `not yet merged` | not_merged | yes (adverb) |
| `been` | `not been merged` | not_merged | yes (adverb) |
| `the` | `not the merged version` | not_merged | no (article + adjective) |
| `a` | `not a merged commit` | not_merged | no (article + adjective) |
| `a single change was` | `not a single change was merged` | merged | no (gap too large) |
| `even the core was` | `not even the core was merged` | merged | no (gap too large) |

The mechanism is a pure distance check, not a linguistic one.

## Impact
The bounded-gap feature is simultaneously too permissive (matches
`not the merged version`, TICKET-058) and too restrictive (misses
`not a single change was merged`, TICKET-057). A log author cannot predict
the outcome without counting tokens. The documented motivation (adverbs
`yet`, `been`) is a subset of what the implementation actually matches.

## Suggestion
Replace the distance-only check with a content-aware check:

1. Whitelist the intervening tokens: match `not` ... `merged` only when the
   intervening tokens are all from a small set of adverbs (`yet`, `been`,
   `actually`, `really`, `ever`, `still`, `just`). This eliminates
   TICKET-058 false positives and is easy to document.
2. Allow a verb phrase: additionally match when the intervening tokens form
   a short passive-verb phrase (`was`, `were`, `is`, `are`, `has`, `have`,
   `had`, `be`, `been`) possibly preceded by an adverb. This covers
   `not yet been merged` and `not actually been merged`.
3. Document the exact contract: if the distance-only check is kept, document
   in the README and module docstring the *exact* set of intervening token
   sequences that match, so a log author can predict the outcome.

Option 1 is the simplest and most predictable. It directly addresses both
TICKET-057 and TICKET-058.
