# TICKET-004: No CI workflow — no automated gate on push to main

## Title
Missing `.github/workflows/` directory and CI configuration; no automated pytest/ruff/mypy gate.

## Evidence
- `find . -type f -not -path './.git/*'` shows no `.github/` directory.
- No `ci.yml`, `main.yml`, or any workflow file exists.
- No `.github/` directory at all.
- The README states "CI green on push" but no workflow is defined.
- `git log --oneline` shows only one commit; no CI badge or workflow history.

## Impact
- No automated verification on push; broken code can land on `main` undetected.
- The "green gate" the mission requires (pytest + ruff + mypy all passing) is not enforced.
- Contributors have no feedback loop; the bootstrap cycle cannot be declared "done" without a passing gate.

## Suggestion
Create `.github/workflows/ci.yml`: