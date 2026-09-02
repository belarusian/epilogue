# TICKET-032: Leading-zero cycle numbers are silently normalized and re-emitted without zeros

**Status: CLOSED (Cycle 9, PR #12).** Documented + pinned (TICKET-032): number parsed as base-10 int, leading zeros dropped and re-emitted normalized. See parser docstring, tests/test_parser.py::test_leading_zero_number_normalized_to_int, tests/test_render.py::test_render_leading_zero_re_emitted_normalized, README 'Cycle header grammar'.

## Title
A header written with leading zeros (`## Cycle 007: Build`) is parsed to the
integer `7` and re-emitted by the renderer as `## Cycle 7: Build` — the zeros
are dropped. The round-trip changes the document's text. This normalization is
neither documented in the module docstring nor pinned by a test.

## Evidence
`epilogue/parser.py:113-116` (`parse_log`) coerces the captured number with
`int(...)`:
    current = Cycle(number=int(header.group(1)), title=header.group(2).strip())
`epilogue/parser.py:14-15` (module docstring) says "``N`` is a non-negative
integer" but does not state that leading zeros are stripped or that the header
is re-emitted in normalized form.

Reproduced against the shipped pipeline (Python 3.10):
    '## Cycle 007: Build\n- x\n'
      parse_log -> Cycle(number=7, title='Build')   (int, zeros dropped)
      render    -> '## Cycle 7: Build'              (re-emitted without zeros)
      render_json -> {"number": 7, ...}             (numeric, zeros dropped)

## Impact
- A log author who writes `## Cycle 007` (a plausible zero-padded style) gets a
  changelog whose header text differs from the source (`## Cycle 7`). The
  round-trip is lossy in a way that is not documented.
- The `--from`/`--to` range filter (`epilogue/cli.py:132`) matches on the
  normalized int, so `--from 7 --to 7` selects a header the user wrote as
  `007`; this is correct but undocumented, and a user who thinks in terms of
  the literal `007` string may be surprised.
- The behavior is untested: `tests/test_parser.py` never uses a leading-zero
  number, so the normalization is invisible to the gate.

## Suggestion
Document the normalization explicitly in `epilogue/parser.py:14-15` (and the
README) — e.g. "the cycle number is parsed as a base-10 integer; leading zeros
are dropped, so `## Cycle 007` is rendered as `## Cycle 7`" — and add a test
pinning that `parse_log('## Cycle 007: Build\n- x\n')[0].number == 7` and that
`render` emits `## Cycle 7: Build`.
Issue: #64
