# TICKET-012: No defined status-marker grammar — MERGED / NO_OP / NOT_MERGED cannot be derived from log text

## Title
The parser (TICKET-011) must classify each entry as MERGED, NO_OP, or
NOT_MERGED, but there is no documented grammar for how those statuses are
encoded in a cycle log, and no sample log is vendored in the repo to pin the
behavior.

## Evidence
- `epilogue/model.py:13-24` — `MergeStatus` defines the three values
  (`MERGED="merged"`, `NO_OP="no_op"`, `NOT_MERGED="not_merged"`), but nothing
  documents which log-text markers map to which value.
- `README.md:3` says the log contains "Rules/Build Order/## Cycle blocks" but
  gives no example of a status marker (e.g. is it `[MERGED]`, `**merged**`,
  `→ merged`, a `Status:` field?).
- `README.md:8` points to the ground-truth log at `../ai/cycle-001-epilogue-gate.md`
  — a path *outside* this repository. `find . -name 'cycle-001*'` returns
  nothing; the log is not vendored, so the parser has no authoritative fixture.
- `tests/test_model.py:58-69` (`test_cycle_holds_entries`) constructs entries
  with explicit `MergeStatus` values, but no test ever derives a status from a
  string — confirming the marker grammar is untested and unspecified.

## Impact
- The "truthfully distinguished" requirement (the mission's core) is
  underspecified: two implementers would invent two different marker grammars.
- Without a vendored sample, the parser cannot be tested against real log
  structure, and the ground-truth log is a moving target outside version
  control.
- The three-way distinction is the whole point of the project; if the grammar
  is ambiguous, the changelog can silently mislabel a NOT_MERGED entry as
  MERGED.

## Suggestion
1. Specify the marker grammar in `docs/LOG_FORMAT.md` (or a section of the
   README): the exact textual form for each of the three statuses, plus the
   `## Cycle N` header form and the entry bullet form.
2. Vendor a minimal, deterministic sample log in the repo (e.g.
   `tests/fixtures/sample_log.md`) covering all three statuses across at least
   two cycles, so the parser has an authoritative, version-controlled fixture.
3. Keep the grammar minimal and stdlib-parseable (regex-friendly); document the
   precedence when multiple markers could apply.

---
Status: CLOSED (Cycle 3, PR #3, merged 6bc0053)
Issue: #47
