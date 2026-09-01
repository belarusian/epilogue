# TICKET-014: CLI never wires the parser — `main()` hardcodes the pending path and never reads the log

## Title
Even once a parser exists (TICKET-011), `epilogue.cli.main()` does not call it:
after validation it unconditionally prints the pending message and returns 3.
The `--log` path is checked for existence but never opened, and there is no
seam to attach parse-to-render.

## Evidence
- `epilogue/cli.py:98-104` — `main()` does `if not args.log.exists():
  parser.error(...)`, then immediately `print(PENDING_MESSAGE, file=sys.stderr)`
  and `return PENDING_EXIT_CODE`. There is no `args.log.read_text()`, no
  `parse_log(...)`, and no `render(...)` call anywhere in the module.
- `epilogue/cli.py:25-31` — `PENDING_EXIT_CODE = 3` and `PENDING_MESSAGE` are
  module-level constants; the pending path is the *only* post-validation path.
- `epilogue/cli.py:34-74` (`build_parser`) defines `--project`, `--from`,
  `--to`, `--log`, but `--project` is never used after parsing (it is only
  validated as present) — it is meant to feed the renderer, which does not
  exist yet.
- `epilogue/__init__.py:14` re-exports only `Cycle`, `Entry`, `MergeStatus`;
  there is no `parse_log` or `render` in the public API to call.

## Impact
- The CLI is a dead end: valid arguments always produce the pending message and
  exit code 3, regardless of log content.
- There is no defined seam for the Build phase: the renderer and the parser
  have no agreed place to attach in `main()`.
- `--project` and the cycle range are validated but discarded, so the
  parse-to-render pipeline has no entry point.

## Suggestion
Define the seam explicitly (do not implement the full pipeline in this ticket):
- In `main()`, after validation, read the log (`args.log.read_text(encoding=
  "utf-8")`) and call `parse_log(text)`; keep the pending message only for the
  *render* step until the renderer lands.
- Decide and document the exit-code contract for the real path: `0` on
  successful render, a distinct non-zero code for parse errors (e.g. a log with
  no cycles in range), keeping `2` for usage errors and reserving `3` or
  reusing it consistently.
- Add the parse/render functions to the `epilogue` public API (`__init__.py`)
  once they exist, so the CLI and tests share one surface.

---
Status: SUPERSEDED (Cycle 26) — the described defect (CLI never wires the parser; main() hardcodes the pending path and never reads the log) was fixed in Cycles 4-5: epilogue/cli.py main() today reads the log (args.log.read_text, guarded since Cycle 20) and wires parse_log -> render/render_json. Historical ticket whose status line was never updated when the work landed; closed as bookkeeping, not re-implemented.
