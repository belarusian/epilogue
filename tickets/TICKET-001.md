# TICKET-001: No Python package layout for `epilogue`

## Title
Missing package directory, `__init__.py`, and module structure for the epilogue CLI.

## Evidence
- `find . -type f -not -path './.git/*'` returns only `README.md` and `.pytest_cache/*`.
- No `epilogue/` directory exists at repo root.
- No `epilogue/__init__.py`, `epilogue/cli.py`, `epilogue/parser.py`, or `epilogue/renderer.py` present.
- `git log --oneline` shows a single commit `c761ec7 bootstrap: epilogue skeleton` that added only `README.md`.
- `.pytest_cache/v/cache/nodeids` contains `[]` — pytest collected zero tests, confirming no importable package exists.

## Impact
- The CLI cannot be invoked (`python -m epilogue` or `epilogue` entry point will fail with `ModuleNotFoundError`).
- No code exists to parse cycle logs or render changelogs; the mission's core capability is entirely absent.
- Downstream tickets (tests, CI, packaging) are blocked until a package skeleton exists.

## Suggestion
Create the following layout:
Issue: #36
