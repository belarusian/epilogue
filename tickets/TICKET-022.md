# TICKET-022: CLI has no `--format` flag — only the human-readable changelog is selectable

## Title
`epilogue.cli.main()` always renders the human-readable changelog. There is no
way to select a machine-readable (JSON) output: the argument parser defines
exactly four flags (`--project`, `--from`, `--to`, `--log`) and `main()` calls
`render(...)` unconditionally. Once `render_json` exists (TICKET-021), the CLI
has no seam to dispatch to it.

## Evidence
- `epilogue/cli.py:33-73` — `build_parser()` adds exactly four arguments:
  `--project` (line 46), `--from` (line 52), `--to` (line 59), `--log` (line
  66). `grep -n "add_argument\|format" epilogue/cli.py` shows no `--format`
  flag and no `choices=` anywhere.
- `epilogue/cli.py:113` — `main()` calls `out = render(selected,
  project=args.project)` unconditionally; there is no branch on an output
  format and no call to any JSON renderer.
- `epilogue/cli.py:1-19` — the module docstring documents the CLI surface as
  `epilogue --project <name> --from <n> --to <m> --log <path>` with no format
  option.

## Impact
- The user cannot obtain structured output from the CLI even after the JSON
  renderer lands; the capability would be reachable only by importing
  `render_json` directly, defeating the purpose of a CLI.
- The exit-code contract and the "no cycles in range" path (exit 1) are
  format-agnostic today but must stay correct for BOTH formats: a JSON
  invocation with no cycles in range should still exit 1 with a clear stderr
  message (not print an empty JSON document and exit 0).

## Suggestion
Extend `build_parser()` and `main()` in `epilogue/cli.py`:
- Add `--format` with `choices=["text", "json"]`, `default="text"`, so existing
  invocations are unchanged (backward compatible).
- In `main()`, after the range filter and the "no cycles in range" check (which
  stays exit 1 for BOTH formats), dispatch:
  - `text` -> `render(selected, project=args.project)` (current behavior).
  - `json` -> `render_json(selected, project=args.project)`.
- Print the chosen output to stdout; keep exit `0` on success, `1` on no cycles
  in range, `2` on usage errors (an invalid `--format` value is a usage error,
  exit 2, via argparse `choices`).
- Update the module docstring and the `--format` help text.
- Update `README.md` Usage to document the new flag and show a JSON example.
---
Status: CLOSED (Cycle 6, PR #9, commit dea16f5)
