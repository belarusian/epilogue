# TICKET-071: `secondary_status` is invisible in the machine-readable JSON output

## Title
Cycle 47 (TICKET-028) added `Entry.secondary_status` so a multi-marker entry's
second status class is no longer silently discarded. But `render_json`
(`epilogue/render.py`) emits only `{"description", "status"}` per entry, so the
new field is invisible to machine consumers. A JSON reader cannot tell that an
entry also carried a second status class.

## Evidence
`epilogue/render.py` `render_json` builds each entry as
`{"description": entry.description, "status": entry.status.value}` — the
`secondary_status` field is never serialized. Reproduced:
    render_json([Cycle(1, "A", [Entry("reverted the no-op", NOT_MERGED, NO_OP)])])
    -> {"cycles": [{"number": 1, "title": "A", "entries":
        [{"description": "reverted the no-op", "status": "not_merged"}]}]}
The `no_op` secondary class is dropped from the JSON document.

## Impact
- The additive signal added in Cycle 47 is only visible in the in-memory model,
  not in the documented machine-readable surface. A downstream tool that
  consumes `--format json` loses the second-marker information that the text
  renderer also does not surface (but the model preserves).
- The JSON contract ("each entry carries `description` and `status`") is now
  incomplete relative to the model.

## Suggestion (bounded, additive)
Emit `secondary_status` in `render_json` as an OPTIONAL key: present only when
`entry.secondary_status is not None`, with the same `.value` token as
`status`. When `None` (the common single-class case) the key is ABSENT, so the
existing pinned JSON shape tests (which assert exact entry dicts for
single-class entries) stay byte-identical. Add a pinned test: a multi-marker
entry emits `"secondary_status": "no_op"`; a single-class entry omits the key.
Issue: #105
