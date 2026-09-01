# TICKET-066: README "Arguments:" list omits the `--status` flag
**Status: CLOSED (Cycle 26, PR #29).** — fixed in the same PR that opened it: the `--status` bullet was added to the README "Arguments:" list and `[--status ...]` to the usage synopsis.

## Title
The CLI defines six arguments, but the README "Arguments:" list under
"## Usage" documents only five — it omits `--status`. A reader of the
canonical argument list cannot discover the status selector from that list
(it is only described in the separate "## Status filter" section).

## Evidence
- `epilogue/cli.py` `build_parser()` defines six `add_argument` calls:
  `--project` (line 56), `--from` (62), `--to` (69), `--log` (76),
  `--format` (82), and `--status` (92).
- `README.md` lines 49-54 ("Arguments:" under "## Usage") list only five:
  `--project`, `--from`, `--to`, `--log`, `--format`. There is no `--status`
  bullet in that list.
- `README.md` line 44 (the usage line) also omits `[--status {merged,no_op,not_merged}]`,
  even though the "## Status filter" section (line 197) and the JSON example
  (line 228) both use it.
- `grep -n "status" README.md` shows `--status` appears only in the
  "## Status filter" section and examples, never in the "Arguments:" list.

## Impact
- The canonical argument reference is incomplete: the documented argument
  list does not match the actual CLI surface. A user reading only "## Usage"
  would not know `--status` exists.
- This is a README/code drift, not a documented design constraint.

## Suggestion
- Add a `--status` bullet to the "Arguments:" list in `README.md` (under
  "## Usage"), describing it as an optional status selector with choices
  `merged`/`no_op`/`not_merged` and default `None` (all entries rendered).
- Optionally add `[--status {merged,no_op,not_merged}]` to the usage line
  (line 44) so the one-line synopsis matches the real CLI.
- No code change; documentation only.
