# TICKET-068: README "Structure" `__init__.py` comment omits `render_json` and `filter_by_status`
**Status: OPEN.**

## Title
The README "Structure" section's `__init__.py` comment lists six public-API
re-exports, but the module actually re-exports eight. `render_json` and
`filter_by_status` are missing from the parenthetical list.

## Evidence
- `epilogue/__init__.py` `__all__` (lines 24-33) contains EIGHT names:
  `Cycle`, `Entry`, `MergeStatus`, `parse_log`, `filter_by_status`, `render`,
  `render_json`, `__version__`.
- The module's own docstring (lines 6-15) lists all eight, including
  `render_json` and `filter_by_status`.
- `README.md` line 13 ("## Structure", `__init__.py` line) reads:
  `# public API re-exports (Cycle, Entry, MergeStatus, parse_log, render,
  __version__)` — only SIX names; `render_json` and `filter_by_status` are
  absent.
- The README "Machine-readable output" section (line 273) explicitly
  references `render_json(cycles, project=None)`, so the function is a
  documented, reachable part of the public API — yet the "Structure" tree
  omits it from the re-export list.
- `filter_by_status` is likewise re-exported and exercised by the CLI
  (`epilogue/cli.py` imports it) and by 42 test references.

## Impact
- The documented public API in "## Structure" understates the real API by two
  names. A reader following the "Structure" tree would not know
  `render_json` / `filter_by_status` are part of the public surface, even
  though both are re-exported, documented elsewhere in the README, and tested.
- This is a README/code drift (same class as TICKET-066/067), not a documented
  design constraint.

## Suggestion
- Update the `__init__.py` comment on `README.md` line 13 to list all eight
  re-exports, matching `__all__` and the module docstring:
  `(Cycle, Entry, MergeStatus, parse_log, filter_by_status, render,
  render_json, __version__)`.
- No code change; documentation only.
