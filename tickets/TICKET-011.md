# TICKET-011: No parser module — the parse capability has no implementation

## Title
The mission's core parse capability — reading a project cycle log into the
`Cycle` / `Entry` / `MergeStatus` data model — has zero implementation. There is
no `epilogue/parser.py` and no `parse_log(...)` function.

## Evidence
- `find epilogue -name '*.py'` returns only `__init__.py`, `__main__.py`,
  `cli.py`, `model.py`. No `parser.py`.
- `epilogue/cli.py:103-104` — after argument validation, `main()` unconditionally
  does `print(PENDING_MESSAGE, file=sys.stderr)` and `return PENDING_EXIT_CODE`
  (3). Nothing reads the log file or builds a `list[Cycle]`.
- `epilogue/model.py:13,28,44` — the data model (`MergeStatus`, `Entry`, `Cycle`)
  exists and is fully tested, but nothing in the package ever *constructs* a
  `Cycle` from text. `grep -rn "Cycle(" epilogue/` matches only `model.py`
  (the class definition) and `tests/test_model.py` (test fixtures).
- `README.md:3` promises the capability: "reads a project cycle log
  (Rules/Build Order/## Cycle blocks) and renders release-note-style changelogs."
- This is the open umbrella ticket TICKET-005 ("No source code — parser,
  renderer, and CLI logic are entirely absent"); this ticket isolates the parse
  half.

## Impact
- The CLI cannot perform its stated function; `--log` is validated for existence
  (`cli.py:98`) but never opened or parsed.
- The three-way truthfulness distinction (MERGED / NO_OP / NOT_MERGED) — the
  core requirement — has a data model but no logic to *derive* a status from log
  text.
- The Build phase has no parse seam to grow on; the renderer and CLI wiring are
  blocked until a parser exists.

## Suggestion
Create `epilogue/parser.py` with a pure, stdlib-only, fully-typed function:

    def parse_log(text: str) -> list[Cycle]: ...

- Parse `## Cycle N` headers into `Cycle(number=N, title=..., entries=[...])`.
- Parse the bullet entries under each header into `Entry(description, status)`.
- Derive `status` from textual markers in the log (see TICKET-012 for the
  marker grammar, which must be specified first).
- Keep it pure (no I/O, no argparse) so it is trivially unit-testable (see
  TICKET-013). Do not wire it into `cli.py` yet (see TICKET-014 for the seam).

---
Status: CLOSED (Cycle 3, PR #3, merged 6bc0053)
Issue: #46
