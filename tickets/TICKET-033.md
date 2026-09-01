# TICKET-033: Header whitespace contract is undocumented — anchored to line start, lenient internally

## Title
The cycle-header regex is anchored to the start of the line (an indented
`## Cycle N` is NOT recognized) but is lenient about internal whitespace
(tabs, multiple spaces, and spaces around the colon are all accepted). This
asymmetric whitespace contract is neither documented in the module docstring
nor pinned by a test.

## Evidence
`epilogue/parser.py:56`:
    _CYCLE_HEADER_RE = re.compile(r"^##\s+Cycle\s+(\d+)\s*:\s*(.*)$")
The `^` anchor plus the absence of any leading-whitespace allowance means a
header must begin at column 0. The `\s+` / `\s*` quantifiers make the internal
whitespace (between `##` and `Cycle`, between `Cycle` and the number, and
around the colon) match any run of whitespace including tabs.

Reproduced against the shipped parser (Python 3.10):
    '  ## Cycle 2: Build\n- x\n'   -> (no cycles)      (indented: rejected)
    '\t## Cycle 2: Build\n- x\n'   -> (no cycles)      (indented: rejected)
    '##  Cycle 2: Build\n- x\n'    -> Cycle(2,'Build') (multi-space: accepted)
    '##\tCycle 2: Build\n- x\n'    -> Cycle(2,'Build') (tab: accepted)
    '## Cycle 2 : Build\n- x\n'    -> Cycle(2,'Build') (space before colon: accepted)
    '## Cycle 2:Build\n- x\n'      -> Cycle(2,'Build') (no space after colon: accepted)

`epilogue/parser.py:10-17` (module docstring) shows the canonical form
`## Cycle N: <title>` but does not state that the header must start at column
0, nor that internal whitespace is flexible.

## Impact
- A log author who indents a cycle header (e.g. inside a nested list or a
  code block) gets a header that is silently NOT parsed — the line is treated
  as a plain line item (or preamble) with no error. This is the most likely
  real-world footgun in the header grammar.
- The lenient internal whitespace means `## Cycle 2:Build` and
  `## Cycle 2 : Build` are both valid, but this is not documented, so an author
  cannot know which forms are safe.
- The behavior is untested: `tests/test_parser.py` only uses the canonical
  single-space form, so neither the anchoring nor the internal leniency is
  pinned.

## Suggestion
Document the exact whitespace contract in `epilogue/parser.py:10-17`:
- State that a header must begin at the start of the line (no leading
  whitespace); an indented `## Cycle N` is not a header.
- State that internal whitespace (between tokens and around the colon) may be
  any run of whitespace, including tabs.
Add tests pinning: an indented header yields no cycle; a tab/multi-space
header yields a cycle; a no-space-after-colon header yields a cycle.
