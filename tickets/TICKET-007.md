# TICKET-007: No `__main__.py` — `python -m epilogue` does not work

## Title
The package cannot be run as a module; `python -m epilogue` fails with
"No module named epilogue.__main__".

## Evidence
- `find . -type f -not -path './.git/*'` shows no `epilogue/__main__.py`.
- `python -m epilogue --help` would fail (no `__main__` submodule).

## Impact
- The mission's "runnable CLI shell" is not reachable via the standard
  `python -m epilogue` invocation.

## Suggestion
Create `epilogue/__main__.py` containing `sys.exit(main())` (importing `main`
from `epilogue.cli`) so `python -m epilogue` works.

---
Status: CLOSED (Cycle 2, PR #2, merged 3dde27a)
Issue: #42
