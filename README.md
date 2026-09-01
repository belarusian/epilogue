# epilogue

CLI that reads a project cycle log (Rules/Build Order/## Cycle blocks) and
renders release-note-style changelogs for a cycle range: `--project`,
`--from`, `--to`; merges vs no-ops vs NOT MERGED distinguished truthfully from
the log; stdlib only; full pytest suite; CI green on push.

Built cycle-by-cycle; see the ground-truth log: `../ai/cycle-001-epilogue-gate.md`

## Structure

    epilogue/
      __init__.py    # public API re-exports (Cycle, Entry, MergeStatus, parse_log, render, __version__)
      model.py       # stdlib data model: MergeStatus enum + Entry/Cycle dataclasses
      parser.py      # parse a raw cycle log into list[Cycle] (pure, stdlib-only)
      render.py      # render list[Cycle] into changelog text (pure, stdlib-only)
      cli.py         # argparse CLI: main(argv) -> int (validation + parse-to-render)
      __main__.py    # `python -m epilogue` entry point -> sys.exit(main())
    tests/
      test_model.py  # data-model tests
      test_parser.py # parser tests
      test_render.py # renderer tests
      test_package.py# importability / public-API tests
      test_cli.py    # CLI tests (help, errors, success, no-cycles-in-range)
    pyproject.toml   # stdlib-only packaging + [project.scripts] epilogue

## The gate

The gate is the single command CI runs on every push and pull request. It must
stay green:

    python3 -m pytest tests/ -x -q && ruff check . && mypy . --ignore-missing-imports

- **pytest** — at least one honest passing test per module.
- **ruff** — lint/format clean (line-length 100, target py310).
- **mypy** — fully typed, no issues.

## Usage

The CLI runs the real parse-to-render pipeline: it reads the cycle log,
parses it into cycles, filters to the requested `--from`/`--to` range, renders
the changelog, and prints it to stdout:

    epilogue --project <name> --from <n> --to <m> --log <path>
    python -m epilogue --project <name> --from <n> --to <m> --log <path>

Arguments:

- `--project` (str, required) — name of the project the log belongs to.
- `--from` (int, required) — first cycle number (inclusive).
- `--to` (int, required) — last cycle number (inclusive); must be `>= --from`.
- `--log` (path, required) — path to the cycle log file; must exist.

Exit codes: `0` on a successful render (changelog on stdout); `2` for usage
errors (missing/invalid args, invalid range, missing log); `1` when no cycles
fall within the requested range (a clear message is printed to stderr).

## Example

Given a log file `log.md`:

```markdown
## Cycle 1: Bootstrap
- Made the gate green
- Laid the skeleton

## Cycle 2: Build
- Added the parser
- No-op: nothing changed
- Abandoned: the old approach
```

Running:

```console
python -m epilogue --project demo --from 1 --to 2 --log log.md
```

prints to stdout:

```text
# demo
## Cycle 1: Bootstrap

### Merged
- Made the gate green
- Laid the skeleton

## Cycle 2: Build

### Merged
- Added the parser
### No-ops
- No-op: nothing changed
### Not Merged
- Abandoned: the old approach
```

The convention: the `# <project>` title is followed immediately by the first cycle header (no blank line); a blank line follows each cycle header; the status sub-sections (`### Merged`, `### No-ops`, `### Not Merged`) are emitted only when non-empty and are not separated by blank lines within a cycle; a blank line separates consecutive cycles. The three statuses stay truthfully distinguishable.
