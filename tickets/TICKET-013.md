# TICKET-013: No parser tests — the gate would pass with the parse capability untested

## Title
The mission requires "at least one honest passing test per module," but there is
no `tests/test_parser.py`, so the parse capability (TICKET-011) would ship with
zero test coverage and the CI gate would still be green.

## Evidence
- `ls tests/` returns `test_cli.py`, `test_model.py`, `test_package.py` — no
  `test_parser.py`.
- `pyproject.toml` `[tool.pytest.ini_options] testpaths = ["tests"]` and the CI
  gate (`.github/workflows/ci.yml`) runs `python3 -m pytest tests/ -x -q`.
  With no parser tests, the gate passes even if `parse_log` is absent or wrong.
- `tests/test_model.py` covers the data model in isolation (field names,
  `default_factory`, the three `MergeStatus` members) but never exercises
  parsing text into `Cycle`/`Entry`.
- `tests/test_cli.py:78-99` (`test_pending_capability_returns_distinct_code_and_message`)
  writes a one-line log (`"## Cycle 1\n"`) and only asserts the pending exit
  code — it does not assert any parsed content, so it cannot catch a broken
  parser.

## Impact
- The core capability would be unverified: a regression in `parse_log` (wrong
  cycle number, dropped entries, mislabeled status) would not fail the gate.
- The "honest passing test per module" requirement is unmet for the new
  `parser.py` module.
- The three-way truthfulness distinction has no regression safety net.

## Suggestion
Create `tests/test_parser.py` (after TICKET-011/012 land) covering at minimum:
- a well-formed log with all three statuses across two cycles parses to the
  expected `list[Cycle]` (numbers, titles, entry counts, and each entry's
  `MergeStatus`);
- the vendored `tests/fixtures/sample_log.md` (TICKET-012) parses to a known
  golden structure;
- edge cases: a log with no `## Cycle` headers, a cycle with no entries, and an
  entry with no recognizable status marker (document the fallback behavior).
Keep every existing test green.

---
Status: OPEN (Cycle 3 audit)
