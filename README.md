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

    epilogue --project <name> --from <n> --to <m> --log <path> [--format {text,json}]
    python -m epilogue --project <name> --from <n> --to <m> --log <path> [--format {text,json}]

Arguments:

- `--project` (str, required) — name of the project the log belongs to.
- `--from` (int, required) — first cycle number (inclusive).
- `--to` (int, required) — last cycle number (inclusive); must be `>= --from`.
- `--log` (path, required) — path to the cycle log file; must exist.
- `--format` (str, optional) — output format: `text` (the default, the
  human-readable changelog) or `json` (a machine-readable document).

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

## Status filter

Pass `--status {merged,no_op,not_merged}` to render only the entries with
that single `MergeStatus`. The selector composes with the range
filter (`--from`/`--to`): the range selects WHICH cycles, the status
selects WHICH entries within them. It applies to both the `text` and
`json` output formats. When omitted (the default), all entries are
rendered, so existing invocations are unchanged.

Given the same `log.md` as the examples above, running:

```console
python -m epilogue --project demo --from 1 --to 2 --log log.md --status not_merged
```

prints to stdout (only the `not_merged` entry survives; cycle 1 is dropped
because it has no `not_merged` entry):

```text
# demo
## Cycle 2: Build

### Not Merged
- Abandoned: the old approach


```

And with `--format json`:

```console
python -m epilogue --project demo --from 1 --to 2 --log log.md --format json --status no_op
```

prints to stdout (a single-line JSON document with only the `no_op` entry):

```json
{"project": "demo", "cycles": [{"number": 2, "title": "Build", "entries": [{"description": "No-op: nothing changed", "status": "no_op"}]}]}
```

Exit codes: `0` when at least one cycle with a matching entry is rendered;
`1` when no cycles fall in the range, or when cycles fall in the range but
none of them has an entry of the requested status (a clear message is
printed to stderr, for both formats); `2` for usage errors (including an
invalid `--status` value).

## Machine-readable output

Pass `--format json` to emit a machine-readable document instead of the
human-readable changelog. The document is a JSON object with a `project` key
and a `cycles` array. Each cycle carries `number`, `title`, and `entries`;
each entry carries `description` and `status`, where `status` is a stable
token: `merged`, `no_op`, or `not_merged`.

Given the same `log.md` as the text example above, running:

```console
python -m epilogue --project demo --from 1 --to 2 --log log.md --format json
```

prints to stdout (a single-line JSON document):

```json
{"project": "demo", "cycles": [{"number": 1, "title": "Bootstrap", "entries": [{"description": "Made the gate green", "status": "merged"}, {"description": "Laid the skeleton", "status": "merged"}]}, {"number": 2, "title": "Build", "entries": [{"description": "Added the parser", "status": "merged"}, {"description": "No-op: nothing changed", "status": "no_op"}, {"description": "Abandoned: the old approach", "status": "not_merged"}]}]}
```

The `project` key is omitted entirely when `--project` is not given (the
literal string `"None"` is never emitted). The three statuses stay truthfully
distinguishable as the stable tokens `merged`, `no_op`, and `not_merged`.
