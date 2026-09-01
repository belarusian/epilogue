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

## Cycle header grammar

Cycles are delimited by lines of the form `## Cycle N: <title>`, where
`N` is a non-negative integer and `<title>` is the rest of the line (which
may be empty). Everything before the first such header is ignored
(preamble). The parser honors the following contracts, so a log author
knows exactly what is safe:

* **Duplicates are kept, in file order.** Two `## Cycle N` headers with the
  *same* number both survive: both are rendered as separate sections, and
  the `--from`/`--to` range filter matches EVERY cycle whose number falls
  in range (so `--from 2 --to 2` returns both).
* **File order, not sorted.** Cycles are emitted in the order their headers
  appear in the file, never sorted by number. A `## Cycle 5` that precedes
  a `## Cycle 3` renders `5` above `3`.
* **Leading zeros are dropped.** The number is parsed as a base-10
  integer, so `## Cycle 007: Build` is rendered as `## Cycle 7: Build`
  (and `render_json` emits `7`).
* **Anchored to line start; lenient internally.** A header must begin at
  the start of the line (column 0); an indented `## Cycle N` (leading
  spaces or a tab) is *not* a header. Internal whitespace is lenient: tabs,
  multiple spaces, and spaces around the colon are all accepted (e.g.
  `##\tCycle 2: Build`, `##  Cycle 2: Build`, `## Cycle 2 : Build`, and
  `## Cycle 2:Build` all parse to number 2).

## Status inference

The parser classifies each log entry into one of the three `MergeStatus`
values (`merged`, `no_op`, `not_merged`) using a deterministic, **token-based**
rule so that the three-way distinction stays truthful. Log authors should know
exactly what the parser honors.

* A **token** is a maximal run of `[a-z0-9-]` in the lowercased description.
  Punctuation such as `:` or `.` separates tokens, but a hyphen is part of a
  token, so `abandoned-cart` is a single token and `no-op` is a single token.
* A **marker** is a phrase (a tuple of tokens). A marker matches only when its
  tokens occur as a **contiguous run** in the description's token list, in
  order, with no other tokens between them — with one documented exception:
  the `not merged` phrase tolerates a *bounded gap* of up to two intervening
  tokens (see the next bullet). Matching is case-insensitive.
* The marker phrases are:

  * `not_merged`: `not merged`, `not-merged`, `un-merged`, `reverted`,
    `reverting`, `reverts`, `abandoned`, `abandoning`, `abandons`
  * `no_op`: `no-op`, `no-ops`, `noops`, `no op`, `no operation`,
    `no operations`, `no change`, `no changes`, `no-changes`
  * `merged`: the default when no `not_merged` or `no_op` marker matches.

  Common morphological variants (verb forms `reverting`/`reverts`,
  `abandoning`/`abandons`; plurals `no-ops`, `no changes`, `no-changes`; and
  the hyphenated compound `not-merged`) are recognized alongside the base
  forms.

* **The `not merged` phrase allows a bounded gap.** Natural phrasings of
  "wasn't merged" insert a word between `not` and `merged` (`yet`, `been`),
  so a strict contiguous run would miss them. For this phrase only, the two
  tokens may be separated by up to two intervening tokens and still match.
  So `not yet merged` and `not been merged` classify as `not_merged`. A gap of
  three or more intervening tokens does **not** match: `not a b c merged`
  (three intervening tokens) defaults to `merged`. Every other marker still
  requires a contiguous run.

* Precedence is `not_merged` > `no_op` > `merged` (default).

Because matching is token-based and requires a contiguous run, a marker word
embedded inside a larger hyphenated word does **not** trigger. For example,
`shipped the abandoned-cart feature` tokenizes to
`[shipped, the, abandoned-cart, feature]`; the `abandoned` marker does not
match because `abandoned-cart` is one token, so the entry is `merged`. In
contrast, `abandoned the renderer` tokenizes to
`[abandoned, the, renderer]` and the `abandoned` marker matches, so the entry
is `not_merged`. Likewise `added a no-op detector` is `no_op` (the `no-op`
token matches), while `no op: nothing changed` is also `no_op` (the `no op`
phrase matches).

Two tokenizer consequences are pinned contracts (so a log author can predict
the outcome):

* **A marker must be a whole token.** A marker glued to a hyphen or a digit on
  either side — `no-op-`, `-no-op`, `no--op`, `no-op2`, `reverted2` — is a
  single token that equals none of the markers, so it defaults to `merged`.
  Punctuation such as `:` or `.` IS a separator, so `no-op:` and `reverted.`
  still match.
* **Non-ASCII characters are dropped, not transliterated.** Accents, CJK, and
  emoji are removed and act as separators, so a marker matches only when its
  exact ASCII stem survives. The same trailing character gives different
  results: `revertedé` is `not_merged` (stem `reverted` is a marker) but
  `abandoné` is `merged` (stem `abandon` is not).

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
