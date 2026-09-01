# TICKET-029: No status selector — the range filter is the only selector

## Title
The CLI can select a cycle RANGE (`--from`/`--to`) but cannot select a
MERGE STATUS. There is no way to render only one `MergeStatus` (e.g. only the
`not_merged` entries) from a log. The range filter is the only selector; a
status selector is a natural new capability that applies to both the `text`
and `json` output formats.

## Evidence
- `epilogue/cli.py:34-84` (`build_parser`) defines exactly four selectors:
  `--project`, `--from`/`--to` (range), `--log`, and `--format {text,json}`.
  There is no `--status` flag. `grep -n "status" epilogue/cli.py` returns
  nothing.
- `epilogue/cli.py:118` — the only selection is the range filter:
  `selected = [c for c in cycles if args.from_cycle <= c.number <= args.to_cycle]`.
  Entries are never filtered by `MergeStatus`.
- `epilogue/render.py` — `render` and `render_json` render every entry of every
  cycle they are given; neither accepts a status selector. The three-way
  distinction is preserved in the output, but a reader cannot isolate one
  status without post-processing the whole changelog.
- `epilogue/model.py` — `Entry.status` is a `MergeStatus` on every entry, so a
  status selector is trivially expressible; only the selector is missing.

## Impact
- A user who wants "show me only the NOT MERGED work in cycles 3..9" must
  render the full range and read the `### Not Merged` sub-sections by eye (text)
  or filter the JSON array by hand (json). There is no first-class selector.
- The capability is orthogonal to the range filter and composes with it:
  range selects WHICH cycles, status selects WHICH entries within them.
- Both output formats benefit: text renders only the matching sub-section;
  json emits only matching entries with their stable status token.

## Suggestion
Add a pure, stdlib-only, fully-typed selector and wire it into the CLI:

    def filter_by_status(cycles: list[Cycle], status: MergeStatus) -> list[Cycle]: ...

- Return NEW `Cycle` objects (do not mutate the input) containing only the
  entries whose `status is status`; drop any cycle that has no matching entry.
  Preserve cycle order and, within a cycle, entry order.
- Add a `--status {merged,no_op,not_merged}` flag to the CLI (default `None` =
  no status filter, backward compatible). The flag value maps to `MergeStatus`
  via its `.value`; an invalid value is a usage error (exit 2 via argparse
  `choices`).
- Apply the status filter AFTER the range filter. Exit-code contract:
  * `0` — at least one cycle with a matching entry is rendered.
  * `1` — no cycles in range (existing) OR cycles in range but none have an
    entry of the requested status (new; clear stderr message).
  * `2` — usage errors (including an invalid `--status` value).
- Re-export `filter_by_status` from `epilogue/__init__.py` and add it to
  `__all__`.
- Document the flag in the README with a byte-verified example.
---
Status: OPEN (Cycle 7, chosen candidate)
