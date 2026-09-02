# TICKET-059: NO_OP false positives - "no change" / "no operation" in context of completed work
**Status: CLOSED (Cycle 25) — documented design constraint, not a defect.** NO_OP markers match anywhere in the description as a contiguous token run; that is the documented contract. `README.md` (lines 172-179) explicitly documents `added a no-op detector` -> `no_op` (the `no-op` token matches regardless of the leading verb `added`), and the parser docstring (lines 107-114) states the same. `confirmed no change needed` -> `no_op` is the direct, documented consequence of the same rule. The ticket's Option 3 ('accept the limitation and document it') is already satisfied. Option 1 (require the marker to lead) / Option 2 (exclude leading verbs) would change the deterministic token-based rule and break `::test_status_no_op_hyphenated_token` and the marker-table enumeration tests; that is a redesign, not a defect fix. No code change.

## Title
The `("no", "change")` and `("no", "operation")` NO_OP markers match
regardless of surrounding context, causing entries that describe completed
work (confirming, verifying, documenting) to be misclassified as NO_OP.

## Evidence
`epilogue/parser.py` lines 148-156:

    _NO_OP_MARKERS: tuple[tuple[str, ...], ...] = (
        ("no-op",),
        ("no-ops",),
        ("no", "op"),
        ("no", "operation"),
        ("no", "operations"),
        ("no", "change"),
        ("no", "changes"),
    )

The matcher (`_has_contiguous_run`, line 190) requires only that the two
tokens `no` and `change` (or `no` and `operation`) appear as a contiguous
run. It does not inspect the surrounding tokens. Empirical probe:

| Description | Tokens | Result | Expected |
|---|---|---|---|
| `confirmed no change needed` | `[confirmed, no, change, needed]` | **no_op** | merged |
| `verified no change in the api` | `[verified, no, change, in, the, api]` | **no_op** | merged |
| `documented that no operation is required` | `[documented, that, no, operation, is, required]` | **no_op** | merged |
| `added a check that no change occurs` | `[added, a, check, that, no, change, occurs]` | **no_op** | merged |

In every case the entry describes work that was done (confirmed, verified,
documented, added). The phrase "no change" / "no operation" is a *finding*
of that work, not a description of the work itself. The entry should be
MERGED (the work was merged), not NO_OP.

Contrast with the intended match:

| Description | Tokens | Result | Expected |
|---|---|---|---|
| `no change` | `[no, change]` | no_op | no_op (correct) |
| `no-op: nothing changed` | `[no-op, nothing, changed]` | no_op | no_op (correct) |

## Impact
A log entry like "confirmed no change needed" is placed under `### No-ops`
in the changelog, implying no work was done. In reality, the work (the
confirmation) was done and merged. This is a truthfulness failure: the
changelog understates the work performed.

## Suggestion
Options:

1. Require the marker to be the entire description (or at least the leading
   tokens): match `no change` / `no operation` only when the description
   *starts* with the marker (after bullet stripping). This eliminates the
   false positives while preserving the intended matches.
2. Exclude entries with a leading verb: if the first token is a known
   past-tense verb (`confirmed`, `verified`, `documented`, `added`,
   `checked`, `tested`, `reviewed`), do not match NO_OP markers. More
   targeted but requires a verb list.
3. Accept the limitation and document it: "the 'no change' and 'no
   operation' markers match anywhere in the description; log authors who
   want to record a confirmation of no change should use a phrasing that
   does not contain the contiguous tokens 'no change' (e.g. 'confirmed
   nothing changed')."

Option 1 is the simplest and most predictable: a log author who writes
"no change" as the entire entry gets NO_OP; a log author who writes
"confirmed no change needed" gets MERGED.

Issue: #92
