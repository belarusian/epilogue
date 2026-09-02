"""Parser for epilogue cycle logs.

This module turns a raw project cycle log (plain text) into a list of
:class:`~epilogue.model.Cycle` objects. It is a pure, stdlib-only function:
no I/O, no argparse, no file reads. The CLI and renderer are separate build
cycles and are intentionally not touched here.

Header grammar
--------------
Cycles are delimited by lines of the form::

    ## Cycle N: <title>

where ``N`` is a non-negative integer and ``<title>`` is the rest of the
line (which may be empty). Everything before the first such header is
ignored (preamble). A new header starts a new cycle.

The grammar is pinned by the following contracts (TICKET-030..033):

* **Duplicates are kept, in file order.** A log with two ``## Cycle N``
  headers of the *same* number keeps BOTH cycles, in file order; both are
  rendered as separate sections. The ``--from``/``--to`` range filter
  matches EVERY cycle whose number falls in range, so ``--from 2 --to 2``
  returns both.
* **File order, not sorted.** Cycles are returned in FILE ORDER, never
  sorted by number. A log with ``## Cycle 5`` before ``## Cycle 3``
  renders 5 above 3. The range filter selects by number but preserves file
  order within the range.
* **Leading zeros are dropped.** The number is parsed as a base-10
  integer, so ``## Cycle 007: Build`` parses to number ``7`` and is
  re-emitted by the renderer as ``## Cycle 7: Build`` (``render_json``
  emits ``7``).
* **Anchored to line start; lenient internally.** A header must begin at
  the START of the line (column 0); an indented ``## Cycle N`` (leading
  spaces or a tab) is NOT a header (yields no cycle). Internal whitespace
  is lenient: tabs, multiple spaces, and spaces around the colon are all
  accepted (e.g. ``##\tCycle 2: Build``, ``##  Cycle 2: Build``,
  ``## Cycle 2 : Build``, and ``## Cycle 2:Build`` all parse to number 2).

Line items
----------
Within a cycle, every non-blank line that is not itself a cycle header
becomes an :class:`~epilogue.model.Entry`. A leading bullet marker (``- ``
or ``* ``) is stripped; the remainder is the entry's ``description``. Plain
non-blank lines (no bullet) are used as-is. Blank lines are skipped.

Explicit status tag (authoritative override)
--------------------------------------------
A log author may pin an entry's status at the source with a **trailing
bracketed tag** at the end of the line::

    - shipped the feature [merged]
    - cleaned up the no-op [no-op]
    - reverted the change [not-merged]

The tag is case-insensitive and accepts a hyphen or underscore between the
two words (``[no-op]`` / ``[no_op]``, ``[not-merged]`` / ``[not_merged]``).
When present it **OVERRIDES** token-based inference and is stripped from the
entry's ``description`` (so the rendered/JSON description no longer carries
the tag). Because the tag is authoritative, no ``secondary_status`` is
recorded for a tagged entry (the inference is not consulted at all). When the
tag is absent, the entry is classified by the token-based inference below,
unchanged. An invalid or unknown tag (e.g. ``[wip]``) is not recognized and is
left in the description, with inference applied as usual.

This is a new, higher-precedence mechanism. The tag is the deliberate,
documented escape hatch that lets the log be authoritative about an entry's
status (TICKET-070). Note the abandon clause of the pinned Cycle 12 contract
A was deliberately amended by TICKET-072 (operator ruling 2026-09-02): an
*untagged* ``abandon`` now infers ``NOT_MERGED`` (it is a ``NOT_MERGED``
marker), so the tag is no longer required to pin it.

Status inference (truthful, deterministic)
------------------------------------------
Each entry's :class:`~epilogue.model.MergeStatus` is inferred from its
description using **token-based** matching, not free substring matching.

* A **token** is a maximal run of ``[a-z0-9-]`` in the lowercased
  description, i.e. ``re.findall(r"[a-z0-9-]+", description.lower())``.
  Punctuation such as ``:`` or ``.`` acts as a separator, but a hyphen is
  part of a token, so ``"abandoned-cart"`` is a single token and
  ``"no-op"`` is a single token. Two consequences of this character class
  are pinned contracts:

  * **Non-ASCII characters are dropped, not folded.** Accented letters, CJK,
    emoji, and any other character outside ``[a-z0-9-]`` are silently removed
    and act as separators. So ``"reverted\u00e9"`` tokenizes to
    ``["reverted"]`` (matches ``NOT_MERGED``) while ``"abandon\u00e9"``
    tokenizes to ``["abandon"]`` (matches ``NOT_MERGED`` since the base form
    ``abandon`` is a marker per TICKET-072) — the outcome of the same trailing
    character depends on whether the ASCII stem happens to be a marker. This
    is intentional: the tokenizer never transliterates, so a marker must
    appear with its exact ASCII spelling.
* A **marker** is a tuple of tokens (a phrase). A marker matches only when
  its tokens occur as a **contiguous run** in the description's token list
  (in order, with no other tokens between them) — with one documented
  exception: the ``("not", "merged")`` phrase tolerates a *bounded gap* of
  up to two intervening tokens (see the next bullet).
* The marker sets (as token tuples) are:

  * ``NOT_MERGED``: ``("not", "merged")``, ``("not-merged",)``,
    ``("not-yet-merged",)``, ``("not-merged-yet",)``,
    ``("un-merged",)``, ``("unmerged",)``, ``("reverted",)``,
    ``("reverting",)``, ``("reverts",)``, ``("revert",)``, ``("abandoned",)``, ``("abandoning",)``,
    ``("abandons",)``, ``("abandon",)``
  * ``NO_OP``: ``("no-op",)``, ``("no-ops",)``, ``("noops",)``,
    ``("no", "op")``, ``("no", "ops")``, ``("no", "operation")``,
    ``("no", "operations")``, ``("no", "change")``, ``("no", "changes")``,
    ``("no-change",)``, ``("no-changes",)``, ``("nothing", "changed")``

  Common morphological variants (verb forms ``reverting``/``reverts``,
  ``abandoning``/``abandons``; plurals ``no-ops``, ``noops``, ``no changes``,
  ``no-changes``; and the hyphenated compounds ``not-merged``,
  ``not-yet-merged``, ``not-merged-yet``) are recognized
  alongside the base forms. A variant is only recognized when it is a whole
  token: a marker glued to a hyphen or digit on either side (``"no-op-"``,
  ``"-no-op"``, ``"no--op"``, ``"no-op2"``, ``"reverted2"``) is one token
  that equals none of the markers and therefore defaults to ``MERGED``.

* **The ``("not", "merged")`` phrase allows a bounded gap.** Natural phrasings
  of "wasn't merged" insert a word between ``not`` and ``merged`` (``yet``,
  ``been``), so a strict contiguous run would miss them. For this phrase only,
  the two tokens may be separated by up to ``_NOT_MERGED_PHRASE_MAX_GAP``
  (two) intervening tokens and still match. So ``"not yet merged"`` and
  ``"not been merged"`` classify as ``NOT_MERGED``. A gap of three or more
  intervening tokens does **not** match: ``"not a b c merged"`` (three
  intervening tokens) defaults to ``MERGED``. Every other marker still
  requires a contiguous run.

* Precedence is ``NOT_MERGED`` > ``NO_OP`` > ``MERGED`` (default). The
  ``MERGED`` status is the deterministic default when no ``NOT_MERGED`` or
  ``NO_OP`` marker matches.

* **Multi-marker entries keep their second marker.** When a description
  carries markers of *both* ``NOT_MERGED`` and ``NO_OP``, the entry's primary
  ``status`` is still chosen by the precedence rule above (``NOT_MERGED``
  wins), but the other class is no longer silently discarded: it is recorded
  on the entry's ``secondary_status`` field. ``secondary_status`` is ``None``
  for the common single-class case. This is additive — it never changes the
  primary ``status`` — so the precedence rule and every pinned contract
  (including the ``abandon`` token-boundary contract) are unchanged. For
  example, ``"reverted the no-op"`` is ``status=NOT_MERGED`` with
  ``secondary_status=NO_OP``.

Because matching is token-based and requires a contiguous run, a marker word
embedded inside a larger hyphenated word does **not** trigger. For example,
``"shipped the abandoned-cart feature"`` tokenizes to
``["shipped", "the", "abandoned-cart", "feature"]``; the ``("abandoned",)``
marker does not match because ``"abandoned-cart"`` is one token, not
``"abandoned"``. Likewise ``"added a no-op detector"`` tokenizes to
``["added", "a", "no-op", "detector"]`` and the ``("no-op",)`` marker
matches, so it classifies as ``NO_OP``. Matching is case-insensitive (the
description is lowercased before tokenizing).
"""

from __future__ import annotations

import re

from epilogue.model import Cycle, Entry, MergeStatus

# A cycle header: "## Cycle N: <title>" (N is an integer, title is the rest
# of the line, possibly empty). Anchored to the start of the line.
_CYCLE_HEADER_RE = re.compile(r"^##\s+Cycle\s+(\d+)\s*:\s*(.*)$")

# Bullet prefixes stripped from line items.
_BULLET_PREFIXES = ("- ", "* ")

# A token is a maximal run of [a-z0-9-] in the lowercased description.
_TOKEN_RE = re.compile(r"[a-z0-9-]+")

# Deterministic, token-based status markers. Each marker is a tuple of
# tokens (a phrase) that must occur as a contiguous run in the description's
# token list. Precedence is NOT_MERGED > NO_OP > MERGED (default).
# Documented in the module docstring.
_NOT_MERGED_MARKERS: tuple[tuple[str, ...], ...] = (
    ("not", "merged"),
    ("not-merged",),
    ("not-yet-merged",),
    ("not-merged-yet",),
    ("un-merged",),
    ("unmerged",),
    ("reverted",),
    ("reverting",),
    ("reverts",),
    ("revert",),
    ("abandoned",),
    ("abandoning",),
    ("abandons",),
    # contract A redesign per TICKET-072 (operator ruling 2026-09-02): the
    # base/imperative form 'abandon' is now a NOT_MERGED marker, matching the
    # other three verb forms of the stem.
    ("abandon",),
)
_NO_OP_MARKERS: tuple[tuple[str, ...], ...] = (
    ("no-op",),
    ("no-ops",),
    ("noops",),
    ("noop",),
    ("no", "op"),
    ("no", "ops"),
    ("no", "operation"),
    ("no", "operations"),
    ("no", "change"),
    ("no", "changes"),
    ("no-change",),
    ("no-changes",),
    ("nothing", "changed"),
)

# The ("not", "merged") phrase is the single marker that tolerates
# intervening words: natural phrasings such as "not yet merged" and "not been
# merged" insert a word between "not" and "merged" but still mean "wasn't
# merged". We allow up to _NOT_MERGED_PHRASE_MAX_GAP intervening tokens
# between the two phrase tokens; a larger gap (e.g. "not a b c merged", three
# intervening tokens) does not match. Documented in the module docstring.
_NOT_MERGED_PHRASE: tuple[str, ...] = ("not", "merged")
_NOT_MERGED_PHRASE_MAX_GAP: int = 2

# Explicit status tag (TICKET-070). A log author may pin an entry's status at
# the source with a TRAILING bracketed tag at the end of the line, e.g.
# "shipped the feature [merged]" or "reverted the change [not-merged]". The
# tag is case-insensitive and accepts a hyphen or underscore between the two
# words. When present it OVERRIDES token-based inference and is stripped from
# the description; when absent, inference is used unchanged. This is a new,
# higher-precedence mechanism. The abandon clause of the pinned Cycle 12
# contract A was deliberately amended by TICKET-072 (operator ruling
# 2026-09-02): an untagged "abandon" now infers NOT_MERGED (it is a
# NOT_MERGED marker), so the tag is no longer required to pin it.
_STATUS_TAG_RE = re.compile(r"\s*\[(merged|no[-_]op|not[-_]merged)\]\s*$", re.IGNORECASE)

# Map the tag's normalized token to a MergeStatus.
_STATUS_TAG_MAP: dict[str, MergeStatus] = {
    "merged": MergeStatus.MERGED,
    "no_op": MergeStatus.NO_OP,
    "not_merged": MergeStatus.NOT_MERGED,
}


def _strip_bullet(line: str) -> str:
    """Return the line with a leading bullet marker (``- `` / ``* ``) removed.

    The line is stripped of surrounding whitespace first. If it begins with a
    bullet prefix, that prefix is removed and the remainder re-stripped.
    """
    stripped = line.strip()
    for prefix in _BULLET_PREFIXES:
        if stripped.startswith(prefix):
            return stripped[len(prefix):].strip()
    return stripped


def _parse_status_tag(
    description: str,
) -> tuple[str, MergeStatus | None]:
    """Split a trailing explicit status tag off a description (TICKET-070).

    Args:
        description: The bullet-stripped entry description.

    Returns:
        A ``(cleaned, status)`` pair. If the description ends with a valid
        explicit status tag (``[merged]`` / ``[no-op]`` / ``[not-merged]``,
        case-insensitive, hyphen or underscore accepted), the tag is removed
        from the description (surrounding whitespace trimmed) and ``status``
        is the corresponding :class:`MergeStatus`. Otherwise the description
        is returned unchanged and ``status`` is ``None`` (the caller then falls
        back to token-based inference). An invalid or unknown tag is NOT
        recognized and is left in place.
    """
    match = _STATUS_TAG_RE.search(description)
    if match is None:
        return description, None
    token = match.group(1).lower().replace("-", "_")
    return description[: match.start()].rstrip(), _STATUS_TAG_MAP[token]


def _tokenize(description: str) -> list[str]:
    """Return the list of tokens in a lowercased description.

    A token is a maximal run of ``[a-z0-9-]``; punctuation (e.g. ``:``)
    separates tokens, while a hyphen is part of a token.
    """
    return _TOKEN_RE.findall(description.lower())


def _has_contiguous_run(tokens: list[str], marker: tuple[str, ...]) -> bool:
    """Return True if ``marker`` occurs as a contiguous run in ``tokens``.

    The marker's tokens must appear in order with no other tokens between
    them. A marker longer than the token list can never match.
    """
    marker_len = len(marker)
    if marker_len == 0 or marker_len > len(tokens):
        return False
    for i in range(len(tokens) - marker_len + 1):
        if tuple(tokens[i:i + marker_len]) == marker:
            return True
    return False


def _has_bounded_gap_run(
    tokens: list[str], marker: tuple[str, ...], max_gap: int
) -> bool:
    """Return True if ``marker`` occurs in ``tokens`` in order with at most
    ``max_gap`` intervening tokens between consecutive marker tokens.

    For ``max_gap == 0`` this is identical to :func:`_has_contiguous_run`.
    A marker longer than the token list can never match.
    """
    marker_len = len(marker)
    if marker_len == 0 or marker_len > len(tokens):
        return False
    if max_gap == 0:
        return _has_contiguous_run(tokens, marker)

    # reachable holds the set of token indices at which the marker can be
    # matched up to the current marker position (the last matched token sits
    # at that index). We keep the full set rather than just the minimum
    # index, because a later occurrence of a marker token can be closer to
    # the next marker token than an earlier one (so the minimum alone is not
    # sufficient to decide reachability).
    reachable: set[int] = {i for i, tok in enumerate(tokens) if tok == marker[0]}
    for pos in range(1, marker_len):
        next_reachable: set[int] = set()
        for j, tok in enumerate(tokens):
            if tok != marker[pos]:
                continue
            # marker[pos] at j is valid if some earlier match of marker[pos-1]
            # sits within max_gap intervening tokens: i in [j-max_gap-1, j-1].
            if any(j - max_gap - 1 <= i <= j - 1 for i in reachable):
                next_reachable.add(j)
        if not next_reachable:
            return False
        reachable = next_reachable
    return bool(reachable)


def _status_classes(description: str) -> set[MergeStatus]:
    """Return the set of status classes whose markers match ``description``.

    This is the *lossless* view of the description: it reports every status
    class (``NOT_MERGED`` and/or ``NO_OP``) that has at least one matching
    marker, rather than collapsing them to a single status. ``MERGED`` is the
    default and is only reported when no ``NOT_MERGED`` or ``NO_OP`` marker
    matches. Matching is token-based and identical to the single-status rule:
    every marker requires a contiguous run except the ``("not", "merged")``
    phrase, which tolerates a bounded gap of up to
    ``_NOT_MERGED_PHRASE_MAX_GAP`` intervening tokens. A marker word embedded
    inside a larger hyphenated token does not trigger.
    """
    tokens = _tokenize(description)
    classes: set[MergeStatus] = set()
    for marker in _NOT_MERGED_MARKERS:
        if marker == _NOT_MERGED_PHRASE:
            if _has_bounded_gap_run(tokens, marker, _NOT_MERGED_PHRASE_MAX_GAP):
                classes.add(MergeStatus.NOT_MERGED)
                break
        elif _has_contiguous_run(tokens, marker):
            classes.add(MergeStatus.NOT_MERGED)
            break
    for marker in _NO_OP_MARKERS:
        if _has_contiguous_run(tokens, marker):
            classes.add(MergeStatus.NO_OP)
            break
    if not classes:
        classes.add(MergeStatus.MERGED)
    return classes


def _infer_statuses(description: str) -> tuple[MergeStatus, MergeStatus | None]:
    """Return ``(primary, secondary)`` for a description.

    The **primary** status is chosen by the documented precedence
    ``NOT_MERGED`` > ``NO_OP`` > ``MERGED`` (default) — this is exactly the
    single-status rule and is unchanged. The **secondary** status is the
    *other* status class present in the description, or ``None`` when the
    description carries at most one status class. This makes a multi-marker
    entry's second marker explicit instead of silently discarded, without
    ever altering the primary status.
    """
    classes = _status_classes(description)
    if len(classes) == 1:
        return next(iter(classes)), None
    # Two classes are present (NOT_MERGED and NO_OP). Pick the primary by the
    # documented precedence; the other is the secondary.
    if MergeStatus.NOT_MERGED in classes:
        primary = MergeStatus.NOT_MERGED
    else:
        primary = MergeStatus.NO_OP
    secondary = next(iter(classes - {primary}))
    return primary, secondary


def _infer_status(description: str) -> MergeStatus:
    """Infer the truthful :class:`MergeStatus` from a description.

    Uses token-based matching against the documented marker sets with
    precedence ``NOT_MERGED`` > ``NO_OP`` > ``MERGED``. Every marker requires
    a contiguous run except the ``("not", "merged")`` phrase, which tolerates
    a bounded gap of up to ``_NOT_MERGED_PHRASE_MAX_GAP`` intervening tokens
    (so "not yet merged" / "not been merged" match). A marker word embedded
    inside a larger hyphenated token does not trigger.

    This returns only the *primary* status; use :func:`_infer_statuses` to
    also recover the secondary status of a multi-marker entry.
    """
    primary, _ = _infer_statuses(description)
    return primary


def parse_log(text: str) -> list[Cycle]:
    """Parse a raw cycle log into an ordered list of :class:`Cycle`.

    Args:
        text: The full text of a project cycle log.

    Returns:
        The cycles in file order. Text that is empty or whitespace-only (or
        contains no cycle header) returns an empty list. Everything before
        the first ``## Cycle N: <title>`` header is ignored.
    """
    cycles: list[Cycle] = []
    current: Cycle | None = None

    for raw_line in text.splitlines():
        header = _CYCLE_HEADER_RE.match(raw_line)
        if header is not None:
            current = Cycle(
                number=int(header.group(1)),
                title=header.group(2).strip(),
            )
            cycles.append(current)
            continue

        # Before the first header there is no cycle to attach entries to.
        if current is None:
            continue

        # Blank lines carry no entry.
        if not raw_line.strip():
            continue

        description = _strip_bullet(raw_line)
        if not description:
            continue

        # Explicit status tag (TICKET-070): when the line ends with a valid
        # trailing [status] tag it OVERRIDES inference and is stripped from the
        # description. The tag is authoritative, so no secondary status is
        # recorded (the inference is not consulted at all). When absent, fall
        # back to the pinned token-based inference (contract A unchanged).
        cleaned, explicit = _parse_status_tag(description)
        if explicit is not None:
            primary, secondary = explicit, None
            description = cleaned
        else:
            primary, secondary = _infer_statuses(description)
        current.entries.append(
            Entry(
                description=description,
                status=primary,
                secondary_status=secondary,
            )
        )

    return cycles
