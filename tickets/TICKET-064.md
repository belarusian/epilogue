# TICKET-064: I/O failures reuse exit code 1, indistinguishable from "no cycles in range"
**Status: CLOSED (Cycle 20, PR #23).**

## Title
Every log I/O failure (directory, invalid UTF-8, unreadable) exits with code 1
— the same code the documented contract reserves for "no cycles in range" — so
a caller cannot distinguish "the log could not be read" from "the range was
empty".

## Evidence
The documented exit-code contract defines exactly three codes:

- `README.md` lines 56-58: "`0` on a successful render ...; `2` for usage
  errors (missing/invalid args, invalid range, missing log); `1` when no cycles
  fall within the requested range (a clear message is printed to stderr)."
- `README.md` lines 233-235 (status section): "`1` when no cycles fall in the
  range, or when cycles fall in the range but none of them has an entry of the
  requested status ...; `2` for usage errors ..."
- `epilogue/cli.py` module docstring lines 14-22 and `main` docstring lines
  108-116: the same three-code contract.

The only exit-1 returns in the code are `epilogue/cli.py` line 140 (no cycles
in range) and line 151 (no matching status); both print a clean `epilogue: ...`
message to stderr.

But the unguarded read at `epilogue/cli.py` line 130 lets `IsADirectoryError` /
`UnicodeDecodeError` / `PermissionError` propagate to the top level.
`epilogue/__main__.py` line 13 does `sys.exit(main())`; an uncaught exception
makes the interpreter exit with code 1 and print a traceback.

Empirical (this audit): all three I/O failure modes exit 1 (see TICKET-061,
TICKET-062, TICKET-063) — the SAME code as "no cycles in range".

## Impact
- A caller (script, CI, agent) that checks the exit code cannot distinguish
  "the log could not be read" (an environment/permission/encoding problem) from
  "the log read fine but no cycles fell in the requested range" (a normal,
  expected outcome). Both are exit 1.
- The documented promise "a clear message is printed to stderr" for exit 1 is
  violated: I/O failures print a raw traceback, not a clear message.
- The exit-code contract is unreliable for automation.

## Suggestion
- Introduce a distinct exit code for I/O failures (e.g. `3` — "log could not be
  read") and document it in `README.md` (both exit-code paragraphs) and the
  `epilogue/cli.py` docstrings.
- Catch the read exceptions (TICKET-061/062/063) and return that code with a
  clean one-line stderr message.
- Keep exit 1 exclusively for "no cycles in range" / "no matching status" and
  exit 2 for usage errors, so the three documented codes stay unambiguous.
- (If a new code is not desired, the minimum fix is to make I/O failures print
  a clean message; but the collision with exit 1 remains, so a distinct code is
  the correct fix.)
