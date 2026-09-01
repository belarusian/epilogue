# TICKET-037: Non-ASCII characters are silently dropped by the tokenizer, producing inconsistent status results

**Status: CLOSED (Cycle 11, PR #15).** Documented + pinned: non-ASCII characters are dropped (not transliterated), so a marker matches only when its exact ASCII stem survives tokenizing. See parser docstring + README 'Status inference'; pinned by tests/test_parser.py::test_status_non_ascii_dropped_not_folded.

## Title
The tokenizer regex `[a-z0-9-]+` matches only ASCII letters, digits, and
hyphens. Any other character (accents, CJK, emoji, etc.) is silently dropped
and acts as a separator. This means a marker word with a trailing non-ASCII
character is truncated to its ASCII stem, and whether it matches depends on
whether that stem happens to be a marker. The same trailing character
produces different statuses for different words.

## Evidence
`epilogue/parser.py:95`:
    _TOKEN_RE = re.compile(r"[a-z0-9-]+")
`epilogue/parser.py:132` (`_tokenize`):
    return _TOKEN_RE.findall(description.lower())
Because the character class excludes non-ASCII, `re.findall` drops those
characters and splits on them.

Reproduced against the shipped code (Python 3.10) — the SAME trailing `é`:
    _infer_status("revertedé")   # -> not_merged  (tokens: ['reverted'])
    _infer_status("no-opé")      # -> no_op       (tokens: ['no-op'])
    _infer_status("abandoné")    # -> merged      (tokens: ['abandon'])
The first two match because their truncated stems (`reverted`, `no-op`) ARE
markers; the third does not because `abandon` is not a marker (the marker is
`abandoned`). The outcome of the same trailing character therefore depends on
the word, which is inconsistent and surprising.

The module docstring (top of `epilogue/parser.py`) defines a token as "a
maximal run of `[a-z0-9-]`" but never states that non-ASCII characters are
dropped, so a reader cannot predict the behavior.

## Impact
- A log author who writes an accented or non-ASCII word adjacent to a marker
  gets a status that depends on an undocumented truncation rule. `revertedé`
  is `not_merged` but `abandoné` is `merged` — the same trailing character,
  opposite outcomes. This is a silent truthfulness failure in the three-way
  distinction.
- The behavior is not pinned by any test: `tests/test_parser.py` never feeds a
  non-ASCII description to the parser, so the drop-and-truncate behavior is
  invisible to the gate.
- The documented token definition ("a maximal run of `[a-z0-9-]`") is
  technically accurate but misleading, because it does not say what happens
  to the characters that are NOT in the class.

## Suggestion
Decide the contract and make it true:
- If non-ASCII characters should be treated as ordinary separators (the
  current behavior), document it explicitly in the module docstring and the
  README "Status inference" section ("characters outside `[a-z0-9-]` are
  dropped and act as separators; a marker must be a whole ASCII token"), and
  add tests pinning `_infer_status("revertedé") is MergeStatus.NOT_MERGED`
  and `_infer_status("abandoné") is MergeStatus.MERGED`.
- If a marker should match regardless of a trailing non-ASCII character,
  normalize the description before tokenizing (e.g. strip non-ASCII or
  Unicode-normalize) in `_tokenize` (`epilogue/parser.py:126-132`) and update
  the docs.
Either way, add a test in `tests/test_parser.py` covering a non-ASCII
description so the contract is pinned by the gate.
