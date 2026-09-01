# TICKET-031: Out-of-order cycle numbers are kept in file order, not sorted

**Status: CLOSED (Cycle 9, PR #12).** Documented + pinned (TICKET-031): cycles emitted in file order, never sorted by number. See parser docstring, tests/test_parser.py::test_out_of_order_numbers_kept_in_file_order_not_sorted, tests/test_render.py::test_render_out_of_order_cycles_in_file_order, README 'Cycle header grammar'.

## Title
The cycle-header grammar returns cycles in file order and never sorts them by
number. A log whose headers appear out of order (e.g. `## Cycle 5` before
`## Cycle 3`) is rendered in that same out-of-order sequence, and the
`--from`/`--to` range filter selects by number but preserves file order. This
is neither documented as a contract nor pinned by a test.

## Evidence
`epilogue/parser.py:111-117` appends cycles in the order headers appear; there
is no sort. `epilogue/parser.py:16-17` (module docstring) says "cycles are
returned in file order" but does not state what happens when file order differs
from numeric order.

Reproduced against the shipped parser (Python 3.10):
    '## Cycle 5: A\n- x\n## Cycle 3: B\n- y\n'
      -> [Cycle(5,'A',[x]), Cycle(3,'B',[y])]   (file order, not sorted)
`epilogue/render.py:84-85` renders them in that order:
    '# demo\n## Cycle 5: A\n\n### Merged\n- x\n\n## Cycle 3: B\n\n### Merged\n- y\n\n'
`epilogue/cli.py:132` range filter preserves file order within the range:
    range 3..5 -> [5, 3]   (selected by number, emitted in file order)

## Impact
- A changelog is expected to read in ascending cycle order; an out-of-order
  log renders `## Cycle 5` above `## Cycle 3`, which is surprising and reads as
  a bug to a human reader.
- The range filter's output order (file order) is not documented, so a machine
  consumer of `render_json` (`epilogue/render.py:138-148`) cannot rely on the
  `cycles` array being sorted by `number`.
- The behavior is untested: `tests/test_parser.py` and `tests/test_render.py`
  only ever use ascending, in-order numbers.

## Suggestion
Decide the contract and pin it:
- If cycles should be sorted by number, sort in `parse_log` (or in the CLI
  before render) and document it; add a test asserting ascending output for an
  out-of-order log.
- If file order is intentional, document in `epilogue/parser.py:16-17` and the
  README that cycles are emitted in file order (NOT sorted) and that the range
  filter preserves file order, and add a test pinning that.
