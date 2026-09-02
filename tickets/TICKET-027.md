# TICKET-027: No explicit status declaration — the log cannot be authoritative about an entry's status

## Title
`epilogue.parser` derives every entry's `MergeStatus` by substring inference
only. There is no grammar for the log to *declare* an entry's status
explicitly, so the log's own words cannot override a mis-inference. The README
claims the statuses are "distinguished truthfully from the log" (line 5), but
in practice the log cannot express status at all — it can only be guessed from
description text.

## Evidence
`epilogue/parser.py:96-133` (`parse_log`) builds each `Entry` with
`status=_infer_status(description)` (line ~130). There is no branch that reads
an explicit status token from the line. `grep -n "tag\|explicit\|override\|declared"
epilogue/parser.py` returns nothing. The only per-line transformation is
`_strip_bullet` (removes a leading `- ` / `* `).

Consequence (reproduced): an entry whose description happens to contain a
marker word is mislabeled (TICKET-024) and there is NO way for the log author
to correct it — e.g. "shipped the abandoned-cart feature" cannot be declared
`merged` because the parser has no syntax for that.

## Impact
- The "truthful" classification is fully determined by fragile substring
  inference with no escape hatch. The log is not the source of truth for
  status; the inference is.
- Any misclassification (TICKET-024/026/028) is uncorrectable at the source,
  forcing a workaround (rewording the description) that couples status to
  prose.
- The README's truthfulness guarantee is weaker than advertised: the log
  cannot assert status, only imply it.

## Suggestion
Add an explicit, optional status tag to the line-item grammar, e.g. a trailing
`[merged]` / `[no-op]` / `[not-merged]` (or a leading `status:` prefix). When
present, it OVERRIDES inference; when absent, fall back to `_infer_status`.
- Update `parse_log` to parse the tag and pass an explicit status to `Entry`.
- Update the module docstring grammar (lines 24-58) and the README to document
  the tag and its precedence over inference.
- Add tests: an explicit tag overrides a conflicting marker word; absence of a
  tag preserves current inference.
Issue: #75
