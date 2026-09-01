# TICKET-017: No renderer tests — the gate would pass with the render capability untested

## Title
The mission requires "at least one honest passing test per module," but there is
no `tests/test_render.py`, so the renderer (TICKET-016) would ship with zero test
coverage and the CI gate (`pytest && ruff && mypy`) would still be green.

## Evidence
- `ls tests/` returns `test_cli.py`, `test_model.py`, `test_package.py`,
  `test_parser.py`. No `test_render.py`.
- `grep -rn "render" tests/` returns nothing — no test imports or exercises any
  render function.
- `epilogue/__init__.py:23-28` — `__all__` has no `render`, so even if a
  `render.py` landed, `test_package.py::test_all_names_are_exported` would not
  catch a missing export unless `render` is added to `__all__` (TICKET-016).
- The gate in `README.md:25-33` is `python3 -m pytest tests/ -x -q && ruff check
  . && mypy . --ignore-missing-imports`; with no render tests, a broken or
  absent renderer does not fail the gate.

## Impact
- The renderer — the half of the pipeline that actually produces the changelog
  the user sees — would have no regression safety net.
- The three-way truthfulness distinction (MERGED / NO_OP / NOT_MERGED) is the
  mission's core; without a test asserting that a NOT_MERGED entry lands in the
  "Not Merged" section (and not "Merged"), a silent mislabel would pass CI.
- The "at least one honest passing test per module" gate requirement is unmet
  for the new `render.py` module.

## Suggestion
Create `tests/test_render.py` (after TICKET-016 lands) covering at minimum:
- a `list[Cycle]` containing all three statuses across two cycles renders to a
  string where each entry appears under its correct status section (assert the
  section headers and that each description is present in the right one);
- `render(cycles, project="demo")` includes the project name; `render(cycles)`
  (no project) does not include the literal string "None";
- `render([])` returns a defined string and does not raise;
- entry order within a section is preserved (deterministic output);
- the output is a `str` and is stable across repeated calls (pure function).
Keep every existing test green.
---
Status: CLOSED (Cycle 4, PR #6, commit 1de4f13)
