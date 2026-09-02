# TICKET-038: Contiguous-run rule rejects natural phrasings with intervening words ("not yet merged")

**Status: CLOSED (Cycle 12, contract A).** FIXED: the `("not","merged")` phrase now tolerates a *bounded gap* of up to two intervening tokens, so natural phrasings `not yet merged` / `not been merged` classify `not_merged`, while a gap of 3+ intervening tokens (e.g. `not a b c merged`) still defaults to `merged`. Implemented via `_NOT_MERGED_PHRASE` / `_NOT_MERGED_PHRASE_MAX_GAP` and `_has_bounded_gap_run` in `epilogue/parser.py` (used only for the `("not","merged")` marker; every other marker keeps the strict contiguous-run rule). See parser docstring + README 'Status inference'; pinned by tests/test_parser.py::test_status_not_merged_phrase_with_intervening_word, ::test_status_not_merged_phrase_with_leading_word_and_intervening_word, ::test_status_not_merged_phrase_with_two_intervening_words, ::test_status_not_merged_phrase_large_gap_defaults_merged, ::test_bounded_gap_run_helper_contract. (Cycle 12, PR #16, commit f597511.)

## Title
The `not merged` marker requires its two tokens to be ADJACENT (a contiguous
run with no other tokens between them). Natural phrasings that insert a word
between the marker's tokens — most commonly `not yet merged`, `not been
merged` — do NOT match and fall through to `MERGED`. The rule is documented
as "contiguous run", but its consequence (that the most common natural
phrasing of "wasn't merged" is missed) is not called out, so a log author
cannot predict it.

## Evidence
`epilogue/parser.py:135-152` (`_has_contiguous_run`) requires the marker's
tokens to appear "in order with no other tokens between them":
    for i in range(len(tokens) - marker_len + 1):
        if tuple(tokens[i:i + marker_len]) == marker:
            return True
The `("not","merged")` marker therefore only matches when `not` and `merged`
are adjacent.

Reproduced against the shipped code (Python 3.10):
    _infer_status("not yet merged")    # -> merged      (tokens: ['not','yet','merged'])
    _infer_status("not been merged")   # -> merged      (tokens: ['not','been','merged'])
    _infer_status("not merged yet")    # -> not_merged  (tokens: ['not','merged','yet'])
    _infer_status("was not merged")    # -> not_merged  (tokens: ['was','not','merged'])
The first two miss because a word (`yet` / `been`) sits BETWEEN `not` and
`merged`; the last two match because the marker tokens are adjacent (extra
words before or after are fine). The same meaning ("wasn't merged") is
classified as `merged` or `not_merged` purely on word order.

The module docstring (top of `epilogue/parser.py`) and the README "Status
inference" section both state the contiguous-run rule, but neither gives an
example of a natural phrasing that FAILS because of it, so the limitation is
invisible to a reader.

## Impact
- `not yet merged` is arguably the most natural way to write "this wasn't
  merged" in a cycle log, and it is classified as `MERGED`. This is a silent
  truthfulness failure in the three-way distinction.
- The outcome depends on word order in a way that is hard to predict:
  `not merged yet` matches, `not yet merged` does not. A log author who
  reorders the same words flips the status.
- No existing test pins the failing phrasing; `tests/test_parser.py:170`
  (`test_status_not_merged_phrase`) only asserts the adjacent form
  `not merged yet` matches, so the intervening-word miss is invisible to the
  gate.

## Suggestion
Decide the contract and make it true:
- If intervening words should not defeat the marker, relax the match for the
  `("not","merged")` phrase (e.g. allow a bounded gap, or match `not` and
  `merged` within a small window) in `_has_contiguous_run`
  (`epilogue/parser.py:135-152`), and update the docs.
- If the strict contiguous-run rule is intentional, document the consequence
  explicitly in the module docstring and the README ("a marker's tokens must
  be adjacent; `not yet merged` does NOT match because `yet` intervenes, so
  it defaults to MERGED") and add a test pinning
  `_infer_status("not yet merged") is MergeStatus.MERGED`.
Either way, add a test in `tests/test_parser.py` covering an intervening-word
phrasing so the contract is pinned by the gate.
Issue: #70
