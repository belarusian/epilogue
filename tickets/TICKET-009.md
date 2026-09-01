# TICKET-009: No CLI tests — `tests/test_cli.py` is absent

## Title
The CLI shell has no tests; the gate would pass with the CLI untested.

## Evidence
- `find . -type f -not -path './.git/*'` shows only `tests/test_model.py` and
  `tests/test_package.py`; no `test_cli.py`.

## Impact
- The mission requirement "at least one honest passing test per module" is unmet
  for the new `cli.py` and `__main__.py` modules.

## Suggestion
Create `tests/test_cli.py` covering: `--help` (exit 0), missing required args
(non-zero), an invalid range `from > to` (non-zero), a missing log path
(non-zero), and the pending-capability path (the distinct exit code + the stderr
message). Keep every existing test green.
