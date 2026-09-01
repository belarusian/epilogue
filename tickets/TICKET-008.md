# TICKET-008: No console-script entry point in `pyproject.toml`

## Title
`pyproject.toml` has no `[project.scripts]` section, so `epilogue` is not a real
console command.

## Evidence
- `pyproject.toml` line 13: "# No console-script entry point yet — the CLI is a
  later build cycle." No `[project.scripts]` table exists.

## Impact
- After `pip install`, there is no `epilogue` command on PATH.

## Suggestion
Add `[project.scripts] epilogue = "epilogue.cli:main"` to `pyproject.toml`.
Keep the package stdlib-only (no new runtime deps).

---
Status: CLOSED (Cycle 2, PR #2, merged 3dde27a)
