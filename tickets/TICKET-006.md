# TICKET-006: No CLI module — `epilogue/cli.py` with `main(argv)` is absent

## Title
The mission's named CLI surface (`--project`, `--from`, `--to`, `--log`) has no
implementation. There is no `epilogue/cli.py` and no `main(argv) -> int`.

## Evidence
- `find . -type f -not -path './.git/*'` shows only `epilogue/__init__.py` and
  `epilogue/model.py`; no `cli.py`.
- `grep -rn "argparse\|def main" epilogue/` returns nothing.
- The README promises a CLI with `--project/--from/--to` but no module provides it.

## Impact
- The package is importable but NOT runnable; there is no entry point to grow on.
- The Build phase (cycles 3-9) has no real seam: parse->render must attach to a
  CLI that does not yet exist.

## Suggestion
Create `epilogue/cli.py` with `main(argv: list[str] | None = None) -> int` using
argparse: `--project` (str, required), `--from` (int, required, `dest="from_cycle"`
because `from` is a keyword), `--to` (int, required), `--log` (path, required).
Validate `from_cycle <= to_cycle` and the log path's existence. After validation,
print a clear "core capability pending (Build phase)" message to stderr and return
a distinct non-zero exit code (e.g. 2). Honest scaffolding, not fake progress.
