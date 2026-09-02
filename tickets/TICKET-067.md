# TICKET-067: README "Structure" section omits `tests/test_main.py`
**Status: CLOSED (Cycle 27, PR #31).** — fixed in the same PR that opened it: the `test_main.py` line was added to the README "Structure" tests/ block.
module (`tests/test_main.py`, subprocess tests for the `python -m epilogue`
entry point) that the README "Structure" tree does not list.

## Title
The README "Structure" section lists five test files, but the repo contains
six. `tests/test_main.py` (which exercises the `python -m epilogue` entry
point end-to-end as a subprocess) is missing from the tree.

## Evidence
- `git ls-files tests/` returns six files: `test_cli.py`, `test_main.py`,
  `test_model.py`, `test_package.py`, `test_parser.py`, `test_render.py`.
- `README.md` lines 20-24 ("tests/" block under "## Structure") list only
  five: `test_model.py`, `test_parser.py`, `test_render.py`, `test_package.py`,
  `test_cli.py`. There is no `test_main.py` line.
- `tests/test_main.py` exists and is non-trivial (71 lines): it invokes
  `python -m epilogue` as a subprocess to prove `sys.exit(main())` in
  `epilogue/__main__.py` works end-to-end.
- `grep -n "test_main" README.md` returns nothing: the file is never
  referenced anywhere in the README.

## Impact
- The documented repo layout does not match the actual layout. A reader of
  "## Structure" would not know the entry point has its own dedicated test
  module, even though `__main__.py` is listed two lines above.
- This is a README/code drift, not a documented design constraint.

## Suggestion
- Add a `test_main.py` line to the "tests/" block in `README.md` (under
  "## Structure"), describing it as the `python -m epilogue` entry-point
  (subprocess) tests.
- No code change; documentation only.

Issue: #100
