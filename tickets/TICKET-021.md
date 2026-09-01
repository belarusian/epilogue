# TICKET-021: No machine-readable (JSON) output — `render_json` is absent

## Title
The renderer emits ONLY the human-readable changelog. There is no
machine-readable output: `epilogue/render.py` defines a single function
`render(cycles, *, project=None) -> str` and nothing in the package produces
JSON. A downstream tool (a dashboard, a CI annotation, a diff of changelogs)
cannot consume the parsed cycles without re-implementing the parse.

## Evidence
- `epilogue/render.py:55` — the only public function is
  `def render(cycles: list[Cycle], *, project: str | None = None) -> str:`.
  `grep -n "json\|def render" epilogue/render.py` matches only that one `def
  render(`; there is no `json` import and no `render_json`.
- `epilogue/__init__.py:21,30` — the public API re-exports `render` only;
  `__all__` is `["Cycle", "Entry", "MergeStatus", "parse_log", "render",
  "__version__"]`. No JSON renderer is exported.
- `epilogue/model.py` — `Cycle`/`Entry`/`MergeStatus` are plain dataclasses and
  an enum, so they are trivially JSON-serializable (`.value` on the enum,
  `dataclasses.asdict` on the dataclasses) — the data model already supports a
  JSON surface; only the renderer is missing.
- `README.md` — documents only the human-readable changelog output; there is no
  machine-readable format described.

## Impact
- The parse-to-render pipeline has exactly one output shape. Any consumer that
  needs structured data (counts per status, per-cycle entries, programmatic
  diffing) must parse the human-readable text back, which is fragile and
  lossy (the text does not carry the cycle number as a number, nor the status
  as a stable token).
- The three-way `MergeStatus` distinction is preserved in the text but not in a
  stable, machine-checkable token; a JSON surface would pin each entry's status
  as its enum value (`"merged"` / `"no_op"` / `"not_merged"`).

## Suggestion
Add a pure, stdlib-only, fully-typed function to `epilogue/render.py`:

    def render_json(cycles: list[Cycle], *, project: str | None = None) -> str: ...

- Return a JSON document (a `str`, via `json.dumps`) that faithfully encodes the
  cycles: an object with an optional `project` key (omitted when `project` is
  `None`, never the literal string `"None"`) and a `cycles` array.
- Each cycle object carries `number` (int), `title` (str), and `entries` (array
  of `{description, status}` where `status` is the enum's `.value` string).
- Preserve cycle order and, within a cycle, entry order.
- Empty `cycles` -> a well-defined document (e.g. `{"cycles": []}`), never
  raises.
- Keep it pure (no I/O, no argparse) so the CLI (TICKET-022) and tests share one
  surface.
- Re-export `render_json` from `epilogue/__init__.py` and add it to `__all__`.
---
Status: CLOSED (Cycle 6, PR #9, commit dea16f5)
