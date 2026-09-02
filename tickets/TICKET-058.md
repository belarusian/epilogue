# TICKET-058: Bounded-gap false positives - "not" + adjective "merged" misclassified as NOT_MERGED
**Status: CLOSED (Cycle 25) — documented design constraint, not a defect.** The bounded-gap matcher is a distance check, not a part-of-speech check; that is the documented contract. `README.md` (lines 161-167) and the parser docstring (lines 93-100) specify `not` ... `merged` matching on token distance only, and `README.md` (lines 172-179) documents that a marker matches on its token run regardless of surrounding words (the `added a no-op detector` example). `not the merged version` matching `not_merged` is the direct, documented consequence. The ticket's Option 3 ('accept the limitation and document it') is already satisfied. Option 1 (adverb whitelist) / Option 2 (passive-verb cue) would change the deterministic token-based rule (Cycle 12, TICKET-038) and break `::test_bounded_gap_run_helper_contract`; that is a redesign, not a defect fix. No code change.

## Title
The bounded-gap matcher for `("not", "merged")` does not distinguish the
passive verb "was not merged" from the adjective "not a merged ...", causing
entries that describe merged work to be misclassified as NOT_MERGED.

## Evidence
`epilogue/parser.py` lines 253-257:

    for marker in _NOT_MERGED_MARKERS:
        if marker == _NOT_MERGED_PHRASE:
            if _has_bounded_gap_run(tokens, marker, _NOT_MERGED_PHRASE_MAX_GAP):
                return MergeStatus.NOT_MERGED

The matcher looks for `not` ... `merged` with <= 2 intervening tokens,
regardless of whether `merged` is a verb (passive: "was not merged") or an
adjective ("not a merged commit"). Empirical probe:

| Description | Tokens | Result | Expected |
|---|---|---|---|
| `not the merged version` | `[not, the, merged, version]` | **not_merged** | merged |
| `not a merged commit` | `[not, a, merged, commit]` | **not_merged** | merged |

In both cases the entry is describing a merged artifact (the merged version,
a merged commit) with a negating modifier. The classifier commits to
NOT_MERGED without any signal that the entry itself was not merged.

Contrast with the intended match:

| Description | Tokens | Result | Expected |
|---|---|---|---|
| `not yet merged` | `[not, yet, merged]` | not_merged | not_merged (correct) |
| `not been merged` | `[not, been, merged]` | not_merged | not_merged (correct) |

## Impact
A log entry like "shipped not a merged commit but a draft" or "reviewed not
the merged version but the PR" is classified NOT_MERGED, placing it under
`### Not Merged` in the changelog. This is a truthfulness failure: the entry
describes work that was done (shipped, reviewed), not work that was
abandoned.

## Suggestion
Options:

1. Restrict the bounded gap to adverbial interveners only: match `not` ...
   `merged` only when the intervening tokens are from a whitelist
   (`yet`, `been`, `actually`, `really`, `ever`). This eliminates the
   adjective false positives while preserving the intended verb matches.
2. Require a passive-verb cue: match `not` ... `merged` only when an
   auxiliary verb (`was`, `were`, `is`, `are`, `has`, `have`, `had`, `be`,
   `been`) appears between `not` and `merged`. More precise but adds
   complexity.
3. Accept the limitation and document it: "the bounded-gap matcher for
   'not ... merged' does not distinguish verb from adjective uses of
   'merged'; log authors should use a single-token marker ('reverted',
   'abandoned') for unambiguous NOT_MERGED entries."

Option 1 is the best balance of precision and simplicity.

Issue: #91
