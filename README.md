# epilogue

CLI that reads a project cycle log (Rules/Build Order/## Cycle blocks) and
renders release-note-style changelogs for a cycle range: `--project`,
`--from`, `--to`; merges vs no-ops vs NOT MERGED distinguished truthfully from
the log; stdlib only; full pytest suite; CI green on push.

Built cycle-by-cycle; see the ground-truth log: `../ai/cycle-001-epilogue-gate.md`

## Structure

    epilogue/
      __init__.py    # public API re-exports (Cycle, Entry, MergeStatus, __version__)
      model.py       # stdlib data model: MergeStatus enum + Entry/Cycle dataclasses
      cli.py         # argparse CLI shell: main(argv) -> int (validation + pending path)
      __main__.py    # `python -m epilogue` entry point -> sys.exit(main())
    tests/
      test_model.py  # data-model tests
      test_package.py# importability / public-API tests
      test_cli.py    # CLI shell tests (help, errors, pending path)
    pyproject.toml   # stdlib-only packaging + [project.scripts] epilogue

## The gate

The gate is the single command CI runs on every push and pull request. It must
stay green:

    python3 -m pytest tests/ -x -q && ruff check . && mypy . --ignore-missing-imports

- **pytest** — at least one honest passing test per module.
- **ruff** — lint/format clean (line-length 100, target py310).
- **mypy** — fully typed, no issues.

## Usage

The CLI shell is wired up and validated, but the core parse-to-render
capability is still pending (a later Build phase). Running it with valid
arguments prints a clear "core capability pending (Build phase)" message to
stderr and exits with a distinct code `3`:

    epilogue --project <name> --from <n> --to <m> --log <path>
    python -m epilogue --project <name> --from <n> --to <m> --log <path>

Arguments:

- `--project` (str, required) — name of the project the log belongs to.
- `--from` (int, required) — first cycle number (inclusive).
- `--to` (int, required) — last cycle number (inclusive); must be `>= --from`.
- `--log` (path, required) — path to the cycle log file; must exist.

Exit codes: `0` for `--help`; `2` for usage errors (missing/invalid args,
invalid range, missing log); `3` for the pending-capability path (distinct from
usage errors, and also reported on stderr).
