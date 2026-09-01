# TICKET-030: Duplicate cycle numbers are silently kept, rendered, and range-matched

**Status: CLOSED (Cycle 9, PR #12).** Documented + pinned (TICKET-030): duplicates kept in file order; range filter matches every in-range number. See parser docstring, tests/test_parser.py::test_duplicate_numbers_kept_in_file_order, tests/test_cli.py::test_range_filter_matches_every_in_range_number_for_duplicate_log, README 'Cycle header grammar'.

## Title
The cycle-header grammar does not reject or deduplicate a log that contains
two `## Cycle N` headers with the same number. Both cycles are kept, both are
rendered as separate sections, and both match the same `--from`/`--to` range.
This behavior is neither documented in the module docstring nor pinned by a
test.

## Evidence
`epilogue/parser.py:111-117` (`parse_log`) appends every header it sees with no
uniqueness check:
    header = _CYCLE_HEADER_RE.match(raw_line)
    if header is not None:
        current = Cycle(number=int(header.group(1)), title=header.group(2).strip())
        cycles.append(current)
`epilogue/parser.py:8-17` (module docstring) says "A new header starts a new
cycle; cycles are returned in file order" but never states what happens when
two headers share a number.

Reproduced against the shipped parser (Python 3.10):
    '## Cycle 2: A\n- x\n## Cycle 2: B\n- y\n'
      -> [Cycle(2,'A',[x]), Cycle(2,'B',[y])]
`epilogue/render.py:84-85` renders both as two `## Cycle 2:` sections:
    '# demo\n## Cycle 2: A\n\n### Merged\n- x\n\n## Cycle 2: B\n\n### Merged\n- y\n\n'
`epilogue/cli.py:132` range filter matches BOTH to the same range:
    [c for c in cycles if args.from_cycle <= c.number <= args.to_cycle]
      -> range 2..2 selects both cycles.

## Impact
- A log with a duplicated cycle number (a plausible authoring mistake) produces
  a changelog with two identically-numbered `## Cycle 2:` sections and no
  signal that the number is duplicated.
- The range filter cannot distinguish the two; `--from 2 --to 2` returns both,
  so a user asking for "cycle 2" gets two cycles.
- The behavior is untested: `tests/test_parser.py` never emits a duplicate
  number, so the gate passes with the behavior unpinned.

## Suggestion
Decide the contract and pin it:
- If duplicates are an error, reject them in `parse_log` (raise) or in the CLI
  (exit 2 with a clear message) and document that.
- If duplicates are allowed, document in `epilogue/parser.py:8-17` that
  duplicate numbers are kept in file order and that the range filter matches
  every cycle whose number falls in range, and add a test pinning the
  parse/render/filter behavior for a duplicate-number log.
