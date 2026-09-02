# TICKET-020: README and module docstrings are stale — they still describe the pending path and exit code 3

## Title
The user-facing and module documentation still describe the CLI as a pending
scaffold that "prints a clear 'core capability pending' message ... and exits
with a distinct code 3." Once TICKET-018 lands the real pipeline and removes the
pending path, these docs are false. The audit rule "documentation must be
accurate" is violated.

## Evidence
- `README.md:36-39` — "The CLI shell is wired up and validated, but the core
  parse-to-render capability is still pending (a later Build phase). Running it
  with valid arguments prints a clear 'core capability pending (Build phase)'
  message to stderr and exits with a distinct code `3`."
- `README.md:51-52` — "Exit codes: `0` for `--help`; `2` for usage errors
  (missing/invalid args, invalid range, missing log); `3` for the
  pending-capability path (distinct from usage errors, and also reported on
  stderr)." There is no `0`-on-success or "no cycles in range" code documented.
- `README.md:15` — Structure comment: `cli.py # argparse CLI shell: main(argv)
  -> int (validation + pending path)`. No `render.py` is listed.
- `README.md:20` — `test_cli.py # CLI shell tests (help, errors, pending path)`.
- `epilogue/cli.py:7-10` — module docstring: "reports that the core
  parse-to-render capability is still pending (a later Build phase) ... it does
  not pretend to render changelogs yet."
- `epilogue/cli.py:83-87` — `main()` docstring: "``3`` for the pending-capability
  path (distinct from usage errors, and also reported on stderr)."
- `epilogue/__init__.py:3-6` — package docstring: "the parse-to-render
  capability is still pending (a later build cycle): the CLI does not yet wire
  the parser into a renderer."
- `epilogue/__init__.py:23-28` — `__all__` lists no `render`, and the docstring's
  public-API list (lines 11-13) omits any renderer.

## Impact
- A newcomer landing at the repo reads that the tool is a non-functional
  scaffold that always exits 3 — the opposite of the post-TICKET-018 reality.
- The exit-code contract documented (0/2/3) does not match the real contract
  (0 on success, 2 usage, distinct code for "no cycles in range").
- The Structure section omits `render.py` and `parser.py` is not listed either,
  so the documented layout does not match the tree.
- The audit rule "documentation must be accurate" is violated in four files.

## Suggestion
After TICKET-016/018 land, update the docs to match the real behavior:
- `README.md` Usage section: describe the real pipeline (reads the log, filters
  to `--from`/`--to`, prints the changelog to stdout) and the real exit-code
  contract: `0` on success, `2` for usage errors, and the distinct non-zero code
  for "no cycles in range". Remove the "pending / code 3" wording.
- `README.md` Structure section: list `parser.py` and `render.py`; update the
  `cli.py` and `test_cli.py` comments to drop "pending path".
- `epilogue/cli.py` module docstring and `main()` docstring: state the real
  pipeline and exit-code contract; remove the pending wording.
- `epilogue/__init__.py` docstring and `__all__`: add `render` to the public API
  and describe the parse-to-render capability as shipped, not pending.
Keep every claim verifiable against the code after the build tickets land.
---
Status: CLOSED (Cycle 4, PR #6, commit 1de4f13)
Issue: #53
