# TICKET-035: Trailing/leading hyphen defeats status-marker matching

**Status: CLOSED (Cycle 11, PR #15).** Subsumed by TICKET-039's pinned contract: a marker glued to a hyphen/digit is one token and defaults to MERGED (documented in parser docstring + README 'Status inference'; pinned by tests/test_parser.py::test_status_marker_glued_to_hyphen_or_digit_defaults_merged).

## Title
A marker token followed by a trailing hyphen (or preceded by a leading hyphen)
is tokenized as a *different* token, so the marker no longer matches and the
entry silently falls through to `MERGED`. The token regex includes `-` as a
token character, so `abandoned-` becomes the single token `abandoned-`, which
is not equal to the marker token `abandoned`.

## Evidence
`epilogue/parser.py:95` defines the tokenizer:
    _TOKEN_RE = re.compile(r"[a-z0-9-]+")
Because `-` is in the character class, a hyphen adjacent to a marker word is
absorbed into the token rather than treated as a separator.

Reproduced against the shipped code (Python 3.10):
    _infer_status("abandoned-")   # -> merged   (tokens: ['abandoned-'])
    _infer_status("-abandoned")   # -> merged   (tokens: ['-abandoned'])
    _infer_status("reverted-")    # -> merged   (tokens: ['reverted-'])
    _infer_status("no-op-")       # -> merged   (tokens: ['no-op-'])
Contrast the clean forms, which DO match:
    _infer_status("abandoned")    # -> not_merged
    _infer_status("reverted")     # -> not_merged
    _infer_status("no-op")        # -> no_op

The marker tables at `epilogue/parser.py:101-111` contain the bare tokens
`("abandoned",)`, `("reverted",)`, `("no-op",)`; none of them match a
hyphen-suffixed/prefixed variant.

## Impact
- A log author who writes a trailing hyphen (e.g. a markdown-style list
  `abandoned-`, or a hyphenated compound `reverted-thing` where the marker is
  the leading part) gets `MERGED` instead of the truthful status, with no
  error. This is exactly the class of "truthful three-way distinction" the
  capability exists to preserve, and it fails silently.
- The failure is asymmetric and surprising: `abandoned` matches but
  `abandoned-` does not, even though the hyphen is clearly not part of the
  word's meaning.
- No existing test pins this: `tests/test_parser.py` covers the clean marker
  forms and the hyphenated-WORD case (`abandoned-cart`, TICKET-030..033 era)
  but never a marker *adjacent* to a stray hyphen.

## Suggestion
Decide the contract and make it true:
- If a stray leading/trailing hyphen should not defeat a marker, normalize
  tokens before matching — e.g. strip leading/trailing `-` from each token in
  `_tokenize` (`epilogue/parser.py:126-132`) so `abandoned-` -> `abandoned`.
  Update the module docstring (the "token" definition at the top of
  `epilogue/parser.py`) to state that boundary hyphens are trimmed.
- If the current behavior is intentional, document it explicitly ("a marker
  must be a whole token; a leading or trailing hyphen makes it a different
  token and will not match") and add a test pinning
  `_infer_status("abandoned-") is MergeStatus.MERGED`.
Either way, add a test in `tests/test_parser.py` covering a marker with a
trailing hyphen so the contract is pinned by the gate.
Issue: #67
