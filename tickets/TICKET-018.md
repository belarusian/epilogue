# TICKET-018: CLI never wires the parser into the renderer — `main()` hardcodes the pending path and never reads the log

## Title
`epilogue.cli.main()` does not perform the mission's parse-to-render pipeline.
After argument validation it unconditionally prints a "pending" message and
returns exit code 3. It never reads the log file, never calls `parse_log`, never
calls `render`, and never prints a changelog to stdout. The `--project` and
`--from`/`--to` arguments are validated but discarded.

## Evidence
- `epilogue/cli.py:98-99` — `main()` does `if not args.log.exists():
  parser.error(...)`, then falls through to the pending path. There is no
  `args.log.read_text(...)` anywhere in the module (`grep -n "read_text"
  epilogue/cli.py` returns nothing).
- `epilogue/cli.py:101-104` — the only post-validation path is
  `print(PENDING_MESSAGE, file=sys.stderr)` and `return PENDING_EXIT_CODE`.
  There is no `parse_log(...)` and no `render(...)` call anywhere in the module
  (`grep -n "parse_log\|render" epilogue/cli.py` matches only docstrings/help).
- `epilogue/cli.py:25-31` — `PENDING_EXIT_CODE = 3` and `PENDING_MESSAGE` are
  module-level constants; the pending path is the *only* post-validation path.
- `epilogue/cli.py:47-52` — `--project` is parsed into `args.project` but is
  never read after `parse_args`; it is meant to feed the renderer, which is not
  called.
- `epilogue/cli.py:53-66` — `--from`/`--to` are parsed into `from_cycle`/
  `to_cycle` and only used for the `from > to` validation at line 92; they are
  never used to filter cycles.
- `epilogue/parser.py:100` — `parse_log(text: str) -> list[Cycle]` exists and is
  exported (`__init__.py:19,27`) but is never imported by `cli.py`.
- `epilogue/render.py` — does not exist (TICKET-016), so there is no renderer to
  call even if the wiring were attempted.

## Impact
- The CLI is a dead end: any valid invocation prints the pending message to
  stderr and exits 3, regardless of log content. The user never sees a changelog.
- The mission's stated behavior — "reads a project cycle log ... and renders
  release-note-style changelogs for a cycle range" (`README.md:3-4`) — is not
  implemented end to end.
- `--project` and the cycle range are validated but discarded, so the
  parse-to-render pipeline has no entry point and no agreed seam.
- The exit-code contract is wrong for the real path: there is no `0`-on-success
  path and no distinct code for "no cycles in range"; the only non-usage code is
  the pending `3`.

## Suggestion
Wire the full pipeline in `main()` (after TICKET-016/017 land the renderer):
- After validation, read the log: `text = args.log.read_text(encoding="utf-8")`.
- Parse: `cycles = parse_log(text)`.
- Filter to the requested range: keep cycles where
  `args.from_cycle <= c.number <= args.to_cycle`.
- Render: `out = render(filtered, project=args.project)`.
- Print the changelog to **stdout** (`print(out)`), not stderr.
- Define and document a real exit-code contract:
  - `0` on success (at least one cycle in range, changelog printed);
  - a distinct non-zero code (e.g. `1`) for "no cycles in range" — print a clear
    message to stderr and return it;
  - keep `2` for usage errors (argparse: missing/invalid args, invalid range,
    missing log path);
  - **remove the pending path entirely** — delete `PENDING_EXIT_CODE`,
    `PENDING_MESSAGE`, and the `print(PENDING_MESSAGE, ...)` / `return
    PENDING_EXIT_CODE` block (lines 25-31, 101-104).
- Update `main()`'s docstring (`cli.py:76-88`) to state the new contract.
- Add `render` to the `epilogue` public API (`__init__.py`) so the CLI and tests
  share one surface (see TICKET-016).
---
Status: CLOSED (Cycle 4, PR #6, commit 1de4f13)
Issue: #51
