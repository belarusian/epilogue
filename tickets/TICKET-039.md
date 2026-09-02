# TICKET-039: A marker glued to a hyphen or digit on either side is one token and falls through to MERGED

**Status: CLOSED (Cycle 11, PR #15).** Documented + pinned: a marker glued to a hyphen or digit on either side is one token that equals no marker and defaults to MERGED; punctuation (: .) is a separator and still matches. See parser docstring + README 'Status inference'; pinned by tests/test_parser.py::test_status_marker_glued_to_hyphen_or_digit_defaults_merged. Subsumes TICKET-035.

## Title
The tokenizer treats a hyphen as part of a token (`[a-z0-9-]+`), so a marker
word that is directly adjacent to a hyphen or a digit on either side is folded
into a single, larger token that does not equal the marker. That entry silently
falls through to `MERGED`. This is a distinct failure mode from TICKET-036
(verb/plural forms like `reverting`, `no-ops`) and TICKET-037 (non-ASCII
characters dropped): here the offending characters are ordinary ASCII hyphens
and digits, and the marker word itself is spelled correctly.

## Evidence
`epilogue/parser.py:95`:
    _TOKEN_RE = re.compile(r"[a-z0-9-]+")
`epilogue/parser.py:132` (`_tokenize`):
    return _TOKEN_RE.findall(description.lower())
Because `-` and digits are inside the character class, a hyphen or digit
immediately next to a marker word is absorbed into the same token, so the
token no longer equals the marker tuple.

Reproduced against the shipped code (Python 3.10):
    _infer_status("no-op-")            # -> merged   (tokens: ['no-op-'])
    _infer_status("-no-op")            # -> merged   (tokens: ['-no-op'])
    _infer_status("no--op")            # -> merged   (tokens: ['no--op'])
    _infer_status("no-op2")            # -> merged   (tokens: ['no-op2'])
    _infer_status("reverted2")         # -> merged   (tokens: ['reverted2'])
    _infer_status("abandoned-")        # -> merged   (tokens: ['abandoned-'])
Contrast the clean forms, which match:
    _infer_status("no-op")             # -> no_op    (tokens: ['no-op'])
    _infer_status("reverted")          # -> not_merged (tokens: ['reverted'])
    _infer_status("no-op: nothing")    # -> no_op    (tokens: ['no-op','nothing'])
A trailing colon or period is a separator (not in the class), so `no-op:` and
`no-op.` still match; only a trailing hyphen or digit breaks the match.

This is distinct from the documented "marker embedded in a larger hyphenated
word does not trigger" example (`abandoned-cart` -> `merged`, pinned by
`tests/test_parser.py:113` `test_status_token_boundary_hyphenated_word_not_merged`).
That example is about a marker word that is a *prefix* of a compound noun. This
ticket is about a *correctly spelled* marker that is merely *adjacent* to a
hyphen or digit — a different authoring mistake (a stray hyphen, a version
suffix, a leading dash) that the current rule also swallows.

## Impact
- A log author who writes a stray trailing hyphen (`no-op-`), a leading dash
  (`-no-op`), a doubled hyphen (`no--op`), or a version/suffix digit
  (`no-op2`, `reverted2`) gets `MERGED` for what is clearly a no-op or a
  reverted change. This is a silent truthfulness failure in the three-way
  distinction, not a crash.
- The break is asymmetric and hard to predict: `no-op:` and `no-op.` match
  (punctuation is a separator) but `no-op-` and `no-op2` do not (hyphen/digit
  are part of the token). A log author cannot tell which trailing characters
  are safe without reading the regex.
- No existing test pins the hyphen/digit-adjacent forms; `tests/test_parser.py`
  only pins the clean forms and the `abandoned-cart` prefix case, so this miss
  is invisible to the gate.

## Suggestion
Decide the contract and make it true:
- If a marker should match even when glued to a hyphen or digit, normalize the
  description before tokenizing in `_tokenize` (`epilogue/parser.py:126-132`)
  — e.g. treat a hyphen as a separator (tokenize on `[a-z0-9]+` and re-join
  hyphenated runs for the `no-op` marker), or strip leading/trailing hyphens
  and trailing digits from each token before matching. Update the module
  docstring's token definition accordingly.
- If exact-token equality is intentional, document the consequence explicitly
  in the module docstring and the README "Status inference" section ("a marker
  must be a whole token; a marker glued to a hyphen or digit on either side —
  `no-op-`, `-no-op`, `no--op`, `no-op2`, `reverted2` — is one token and does
  NOT match, so it defaults to MERGED; punctuation such as `:` or `.` is a
  separator and does not break the match") and add tests pinning
  `_infer_status("no-op-") is MergeStatus.MERGED`,
  `_infer_status("-no-op") is MergeStatus.MERGED`, and
  `_infer_status("reverted2") is MergeStatus.MERGED`.
Either way, add tests in `tests/test_parser.py` covering hyphen/digit-adjacent
markers so the contract is pinned by the gate.
Issue: #14
