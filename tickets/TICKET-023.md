# TICKET-023: No tests pin the JSON output — a regression in `render_json`/`--format json` would not fail the gate

## Title
There is no test for the machine-readable output. `tests/` has no reference to
`json` or `render_json` (the only `format` hit is a docstring in
`test_render.py:169`). Once TICKET-021/022 land, the new capability would ship
untested: a regression that drops a cycle, mislabels a status, or prints the
literal `"None"` for a missing project would pass the gate (pytest/ruff/mypy)
silently.

## Evidence
- `grep -rn "json\|render_json" tests/` returns nothing (only a false-positive
  `format` in `tests/test_render.py:169`, a docstring about header format).
- `tests/test_render.py` — 9 tests, all exercise `render` (the text renderer);
  none construct a JSON document or assert on `json.loads` output.
- `tests/test_cli.py` — 11 tests, all invoke the CLI with the text output; none
  pass `--format json` or assert on JSON stdout.
- `tests/test_main.py` — 3 subprocess tests, all text output.

## Impact
- The three-way `MergeStatus` distinction is the mission's core truthfulness
  requirement. In JSON it is carried as a stable token (`"merged"` / `"no_op"`
  / `"not_merged"`); without a test, nothing pins that a `NOT_MERGED` entry is
  emitted as `"not_merged"` and not collapsed to `"merged"`.
- The "no cycles in range" exit-1 contract must hold for the JSON path too;
  without a test, a regression that prints `{"cycles": []}` and exits 0 for an
  out-of-range query would not be caught.

## Suggestion
Add honest tests (small inline `Cycle`/`Entry` objects and `tmp_path` logs —
never the real ground-truth log):
- `tests/test_render.py` (extend) — `render_json` tests:
  - multi-cycle, all three statuses: `json.loads` the output and assert the
    exact structure (cycle numbers, titles, per-entry `description` + `status`
    token) and that each status lands as its own token (truthfulness).
  - `project` present -> `project` key equals the name; `project` is `None` ->
    the key is ABSENT (never the literal string `"None"`).
  - empty `cycles` -> a well-defined document (e.g. `{"cycles": []}`), no raise.
  - cycle order and entry order preserved.
- `tests/test_cli.py` (extend) — `--format json` tests:
  - success: exit 0, stdout is valid JSON with the expected cycles.
  - no cycles in range: exit 1, clear stderr message (NOT an empty JSON doc +
    exit 0).
  - invalid `--format` value: exit 2 (argparse usage error).
  - default (no `--format`) still yields the human-readable text (backward
    compatible).
- Keep every existing test green.
---
Status: CLOSED (Cycle 6, PR #9, commit dea16f5)
