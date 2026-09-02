# TICKET-070: No explicit status declaration — the log cannot be authoritative about an entry's status

## Title
`epilogue.parser` derives every entry's `MergeStatus` by token-based substring
inference only. There is no grammar for the log to *declare* an entry's status
explicitly, so the log's own words cannot override a mis-inference. The README
claims the statuses are "distinguished truthfully from the log" (line 5), but
in practice the log cannot express status at all — it can only be guessed from
description text.

## Evidence
`epilogue/parser.py:337-382` (`parse_log`) builds each `Entry` with
`primary, secondary = _infer_statuses(description)` (line ~373). There is no
branch that reads an explicit status token from the line. The only per-line
transformations are `_strip_bullet` (removes a leading `- ` / `* `) and
`_tokenize`. `grep -n "tag\|explicit\|override\|declared" epilogue/parser.py`
returns nothing.

Consequence (reproduced): an entry whose description happens to contain a
marker word is mislabeled and there is NO way for the log author to correct it
at the source — e.g. "shipped the abandoned-cart feature" is `MERGED` (correct
here, but by luck of token boundaries), while a genuinely-merged entry that
mentions "reverted" would be forced to `NOT_MERGED` with no escape hatch.

## Impact
- The "truthful" classification is fully determined by fragile token inference
  with no escape hatch. The log is not the source of truth for status; the
  inference is.
- Any misclassification is uncorrectable at the source, forcing a workaround
  (rewording the description) that couples status to prose.
- The README's truthfulness guarantee is weaker than advertised: the log
  cannot assert status, only imply it.

## Suggestion (deliberate, ticketed redesign of the status contract)
Add an explicit, optional **trailing status tag** to the line-item grammar:
a trailing `[merged]` / `[no-op]` / `[not-merged]` (case-insensitive, hyphen
or underscore accepted) at the END of the line. When present it OVERRIDES
inference and is stripped from the description; when absent, the current
token-based inference is used unchanged.

This is the only legitimate path to also unblock `abandon` in TICKET-041/#78:
it re-opens the status contract ON PURPOSE with a full test suite, but it does
NOT change the pinned Cycle 12 contract A — `abandon` still *infers* `MERGED`
when no tag is present. The tag is a new, higher-precedence mechanism, not a
smuggled change to the inference table.

- Update `parse_log` to detect and strip the tag and pass an explicit status
  to `Entry` (falling back to `_infer_statuses` when absent).
- Update the module docstring grammar and the README to document the tag and
  its precedence over inference.
- Add tests: an explicit tag overrides a conflicting marker word; absence of a
  tag preserves current inference (including contract A: `abandon` -> MERGED);
  the tag is stripped from the description; an invalid/unknown tag is ignored
  (falls back to inference).
Issue: #75
Issue: #104
