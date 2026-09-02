# TICKET-005: No source code — parser, renderer, and CLI logic are entirely absent

## Title
The core capability (parse cycle log → render changelog distinguishing merges / no-ops / NOT MERGED) has zero implementation.

## Evidence
- `find . -type f -not -path './.git/*'` returns only `README.md` and `.pytest_cache/*`.
- No `.py` files exist anywhere in the repository.
- The README describes the capability: "reads a project cycle log (Rules/Build Order/## Cycle blocks) and renders release-note-style changelogs for a cycle range: --project, --from, --to; merges vs no-ops vs NOT MERGED distinguished truthfully from the log."
- No parser logic, no renderer logic, no argument handling, no data model for a "cycle" or a "merge status" exists.
- The referenced ground-truth log `../ai/cycle-001-epilogue-gate.md` is outside this repo and not vendored.

## Impact
- The CLI cannot perform its stated function; there is nothing to run.
- The three-way distinction (merged / no-op / NOT MERGED) — the core truthfulness requirement — has no data model or logic.
- All other tickets (package layout, tests, CI, packaging) are scaffolding around an empty core; they are necessary but not sufficient.

## Suggestion
Implement in `epilogue/` (after TICKET-001 creates the layout):

1. **`epilogue/parser.py`** — a function `parse_log(text: str) -> list[Cycle]` where `Cycle` is a `dataclass` with fields: `number: int`, `title: str`, `entries: list[Entry]`. `Entry` has `description: str`, `status: MergeStatus` (enum: `MERGED`, `NO_OP`, `NOT_MERGED`). Parse `## Cycle N` headers and bullet entries, inferring status from markers in the log text.

2. **`epilogue/renderer.py`** — a function `render(cycles: list[Cycle], from_cycle: int, to_cycle: int, project: str) -> str` producing markdown release notes. Must visibly separate the three statuses (e.g., sections "Merged", "No-ops", "Not Merged").

3. **`epilogue/cli.py`** — `main()` using `argparse` with `--project` (str), `--from` (int), `--to` (int), and a positional or `--log` path. Reads the log file, calls parser, calls renderer, prints to stdout. Exit code 0 on success, 1 on parse error or out-of-range cycle.

All code stdlib-only. Type-annotated for mypy strict.
Issue: #40
