# TICKET-019: CLI tests pin the pending path — they will break when the real pipeline lands

## Title
`tests/test_cli.py` asserts the current pending-capability behavior (exit code 3
+ `PENDING_MESSAGE` on stderr). When TICKET-018 removes the pending path and
wires the real parse-to-render pipeline, these tests will fail, and there are no
tests covering the real behavior (stdout changelog, `0` on success, the
"no cycles in range" code).

## Evidence
- `tests/test_cli.py:13` — `from epilogue.cli import PENDING_EXIT_CODE,
  PENDING_MESSAGE, main`. The test module imports the two pending-path constants
  that TICKET-018 deletes.
- `tests/test_cli.py:90-110` — `test_pending_capability_returns_distinct_code_and_message`
  calls `main([...])` with valid args and asserts `code == PENDING_EXIT_CODE`,
  `code != 0`, and `PENDING_MESSAGE in err`. This test directly encodes the
  pending path that must be removed.
- `tests/test_cli.py:1-6` — the module docstring describes the suite as
  "argparse + validation + pending path"; the suite has no test that asserts a
  changelog is printed to stdout, no test for exit `0` on success, and no test
  for the "no cycles in range" code.
- `epilogue/cli.py:25-31` — `PENDING_EXIT_CODE` / `PENDING_MESSAGE` are the only
  non-usage exit codes today; the real-path codes (`0`, and a distinct code for
  "no cycles in range") do not exist yet (TICKET-018).

## Impact
- Landing TICKET-018 without updating this file breaks the gate: the import at
  line 13 fails (constants removed) and `test_pending_capability_...` fails.
- The real pipeline — the mission's actual behavior — would ship with no test
  coverage: nothing asserts the changelog reaches stdout, that success is exit
  `0`, or that an empty range yields the distinct non-zero code.
- The "at least one honest passing test per module" gate requirement is met only
  for the *old* behavior, not the new one.

## Suggestion
Rewrite `tests/test_cli.py` (after TICKET-018 lands) to cover the real contract:
- remove the `PENDING_EXIT_CODE` / `PENDING_MESSAGE` imports and the
  `test_pending_capability_...` test;
- keep the usage-error tests (`--help` exits 0, missing args, invalid range,
  missing log path) — these still hold;
- add a success test: a temp log with cycles in range → `main` returns `0` and
  the rendered changelog (including the project name and the correct status
  sections) is on **stdout**;
- add a "no cycles in range" test: a log whose cycles fall outside
  `--from`/`--to` → `main` returns the distinct non-zero code and a clear
  message is on stderr;
- add a test that `--project` is reflected in the output (it is now used, not
  discarded).
Keep every other module's tests green.
---
Status: CLOSED (Cycle 4, PR #6, commit 1de4f13)
