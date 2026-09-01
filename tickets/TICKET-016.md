# TICKET-016: No renderer module — `render(cycles, *, project=None) -> str` is absent

## Title
The mission's core RENDERER capability — turning a parsed `list[Cycle]` into
release-note-style changelog text that truthfully distinguishes MERGED / NO_OP /
NOT_MERGED — has zero implementation. There is no `epilogue/render.py` and no
`render(...)` function anywhere in the package.

## Evidence
- `ls epilogue/` returns only `__init__.py`, `__main__.py`, `cli.py`, `model.py`,
  `parser.py`. No `render.py`.
- `grep -rn "render" epilogue/` matches only docstrings and help text
  (`cli.py:8,10,29,43,58,65`, `model.py:7`, `parser.py:5`, `__init__.py:1,4,6`)
  — there is no `def render(` and no module that produces changelog text.
- `epilogue/__init__.py:23-28` — `__all__` is `["Cycle", "Entry", "MergeStatus",
  "parse_log", "__version__"]`. There is no `render` in the public API.
- `epilogue/model.py:13-24` and `epilogue/parser.py:100-140` — the three-way
  `MergeStatus` and the parser that *derives* a status from log text both exist
  and are tested, but nothing consumes them to emit text. The pipeline stops at
  `list[Cycle]`.
- `README.md:3-4` promises the capability: "renders release-note-style
  changelogs for a cycle range ... merges vs no-ops vs NOT MERGED distinguished
  truthfully from the log."

## Impact
- The parse half (TICKET-011, closed) has no consumer: `parse_log` returns
  `list[Cycle]` but there is no function to turn that into the changelog the
  CLI is supposed to print.
- The three-way truthfulness distinction — the mission's core — is modeled and
  parsed but never *rendered*; a NOT_MERGED entry and a MERGED entry are
  indistinguishable in any output because there is no output.
- The CLI wiring (TICKET-018) is blocked: `main()` has nothing to call after
  `parse_log`.

## Suggestion
Create `epilogue/render.py` with a pure, stdlib-only, fully-typed function:

    def render(cycles: list[Cycle], *, project: str | None = None) -> str: ...

- Group each cycle's entries by `MergeStatus` and emit three clearly labeled
  sections (e.g. "Merged", "No-ops", "Not Merged") so the three-way distinction
  is visible in the output.
- `project` is keyword-only and optional: when provided, include it in a header
  line; when `None`, omit it (do not print the literal string "None").
- Handle the empty case: `render([])` returns a well-defined string (e.g. an
  empty or "no cycles" placeholder), never raises.
- Preserve entry order within each status section; keep it deterministic so it
  is trivially unit-testable (see TICKET-017).
- Do NOT do I/O, argparse, or file reads — keep it a pure function of its
  inputs so the CLI (TICKET-018) and tests share one surface.
---
Status: CLOSED (Cycle 4, PR #6, commit 1de4f13)
