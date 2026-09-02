# TICKET-057: Bounded-gap false negatives - natural "not ... merged" phrasings with 3+ intervening tokens default to MERGED
**Status: CLOSED (Cycle 25) — documented design constraint, not a defect.** The bounded-gap cap of two intervening tokens is the *specified* rule: `epilogue/parser.py` docstring (lines 93-100) and `README.md` 'Status inference' (lines 161-167) both state that a gap of three or more intervening tokens does **not** match and defaults to `merged` (the documented example is `not a b c merged`). This behavior is pinned by `tests/test_parser.py::test_status_not_merged_phrase_large_gap_defaults_merged` and `::test_bounded_gap_run_helper_contract`. The ticket's own Option 3 ('accept the limitation and document it') is already satisfied by that documentation. Raising the cap (Option 1) or adding a whitelist (Option 2) would change the deterministic token-based contract chosen in Cycle 12 (TICKET-038, 'contract A') and break the pinned tests; it is a redesign, not a defect fix. No code change.

## Title
The `("not", "merged")` bounded-gap cap of 2 intervening tokens causes
common natural-language phrasings of "wasn't merged" to be misclassified as
MERGED.

## Evidence
`epilogue/parser.py` line 165:

    _NOT_MERGED_PHRASE_MAX_GAP: int = 2

The bounded-gap matcher (`_has_bounded_gap_run`, line 205) allows at most 2
intervening tokens between `not` and `merged`. Empirical probe:

| Description | Tokens | Result | Expected |
|---|---|---|---|
| `not a single change was merged` | `[not, a, single, change, was, merged]` | **merged** | not_merged |
| `not one of the changes was merged` | `[not, one, of, the, changes, was, merged]` | **merged** | not_merged |
| `not even the core was merged` | `[not, even, the, core, was, merged]` | **merged** | not_merged |
| `not a single line was merged` | `[not, a, single, line, was, merged]` | **merged** | not_merged |
| `not the final version was merged` | `[not, the, final, version, was, merged]` | **merged** | not_merged |

In every case the gap between `not` and `merged` is 3 or more tokens, so the
bounded-gap matcher rejects the match and the entry falls through to the
MERGED default.

The documented example of a non-matching gap is `not a b c merged` (three
intervening tokens: `a`, `b`, `c`), which is a contrived string. The
phrasings above are natural English.

## Impact
The core truthfulness requirement - distinguishing MERGED from NOT_MERGED -
is violated for a common class of log entries. A log author who writes
"not a single change was merged" (meaning: nothing was merged) gets a
changelog that lists the entry under `### Merged`, which is the opposite of
the truth.

## Suggestion
Options (pick one, document the choice):

1. Raise the gap cap to 4 or 5 to cover the common phrasings above.
   Document the new cap and the new non-matching boundary.
2. Replace the bounded gap with a more targeted rule: match `not` ...
   `merged` when the intervening tokens are a small whitelist of adverbs
   (`yet`, `been`, `even`, `actually`, `really`) or a short verb phrase
   (`a single`, `one of the`, `the final`). More precise but more complex.
3. Accept the limitation and document it explicitly in the README and
   module docstring: "phrasings of 'not ... merged' with more than two
   intervening tokens are NOT recognized and default to MERGED; log authors
   should use a shorter phrasing (e.g. 'not merged', 'not yet merged') or
   a single-token marker (e.g. 'reverted', 'abandoned')."

Option 3 is the lowest-risk: it does not change behavior, only documents the
existing contract so log authors can avoid the footgun.

Issue: #90
