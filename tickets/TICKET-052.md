# TICKET-052: I/O errors exit 1, colliding with the documented "no cycles in range" code
**Status: CLOSED (Cycle 24) — superseded by TICKET-064 (Cycle 20, PR #23).** I/O read failures now exit `3` (documented in the `cli.py` module docstring and the README "Exit codes" section), distinct from `1` (no cycles in range / no matching status) and `2` (usage errors). The exit-code collision described here was resolved in Cycle 20; this ticket is a duplicate of the already-closed 064; no code change was needed in Cycle 24.


## Title
The CLI's documented exit-code contract reserves `1` for "no cycles fall within
the requested range" (and, with `--status`, "no matching entry") and `2` for
usage errors. But the unguarded `read_text` (TICKET-051) lets I/O failures
(`IsADirectoryError`, `UnicodeDecodeError`, `PermissionError`) propagate, and
Python exits with code `1` for any uncaught exception. So an I/O error — which is
neither "no cycles in range" nor a usage error — is reported with the same exit
code as "no cycles in range".

## Evidence
Documented contract, `epilogue/cli.py` module docstring and README "Exit codes"
(README lines 56-57):
    * 0 — successful render
    * 1 — no cycles fall within the requested range, OR ... no entry of the requested --status
    * 2 — usage errors (missing/invalid arguments, an invalid cycle range,
          an invalid --status value, or a missing log path)

Observed: the three I/O failures from TICKET-051 all exit `1` (reproduced:
`EXIT=1` with a traceback for a directory, an invalid-UTF-8 log, and a
`chmod 000` file). The `1` here is Python's default uncaught-exception code, not
the intentional `return 1` at `cli.py:140` / `cli.py:151`.

## Impact
- Automation that distinguishes "nothing to render" (exit `1`, benign) from
  "the log could not be read" (a real failure) cannot do so: both are `1`.
- A CI step or shell script that treats exit `1` as "no cycles, skip" will
  silently swallow a log it actually failed to read, producing an empty result
  with no signal that the input was unreadable.
- The contract is now under-specified: there is no documented code for I/O
  failure, and the observed code (`1`) is misleading.

## Suggestion
Give I/O failure its own, documented exit code. The cleanest fit is `2` (a
"cannot use the provided input" usage error), emitted via `parser.error(...)`
once TICKET-051's guard is in place. Update the `cli.py` module docstring and the
README "Exit codes" sections to state that an unreadable / non-UTF-8 / directory
log is a usage error (exit `2`). Add a test asserting the exit code (TICKET-055).

Issue: #85
