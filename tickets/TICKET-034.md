# TICKET-034: `filter_by_status` returns aliased `Entry` objects — mutating a returned entry mutates the input

## Title
The status-filter capability (`filter_by_status`) returns NEW `Cycle` objects
but reuses the SAME `Entry` objects from the input. A caller who mutates a
returned entry (e.g. `result[0].entries[0].description = ...`) silently mutates
the original cycle's entry. The docstring claims the function "never mutates
the input list or its cycles" and returns "a NEW list of NEW `Cycle` objects",
which a reader reasonably takes to mean the returned structure is independent —
but the entries are shared by reference.

## Evidence
`epilogue/render.py:173-178` (`filter_by_status`) builds the result by
collecting the *existing* entry objects and wrapping them in new `Cycle`
shells:
    matching = [entry for entry in cycle.entries if entry.status is status]
    if not matching:
        continue
    result.append(
        Cycle(number=cycle.number, title=cycle.title, entries=matching)
    )
`matching` is a list of the same `Entry` instances that live in
`cycle.entries`; only the `Cycle` container is new.

The docstring at `epilogue/render.py:155-158` states:
    "it returns a NEW list of NEW :class:`Cycle` objects and never mutates
    the input list or its cycles."
and `epilogue/render.py:43-44` (module docstring) repeats "a NEW list of NEW
:class:`Cycle` objects". Neither states that the `Entry` objects are shared
by reference, so the "new" guarantee is scoped to `Cycle` only and is not
spelled out.

Reproduced against the shipped code (Python 3.10):
    c = Cycle(1, "A", [Entry("x", MergeStatus.MERGED),
                       Entry("y", MergeStatus.NO_OP)])
    f = filter_by_status([c], MergeStatus.MERGED)
    f[0].entries[0] is c.entries[0]   # True  (aliased)
    f[0].entries[0].description = "MUTATED"
    c.entries[0].description          # 'MUTATED'  (input mutated)

The existing test `tests/test_render.py:368`
(`test_filter_by_status_does_not_mutate_input`) only asserts that the *call
itself* leaves the input unchanged; it never asserts that the returned entries
are independent of the input, so the aliasing is invisible to the gate.
`tests/test_render.py:395` (`test_filter_by_status_returns_new_cycle_objects`)
asserts `returned.entries is not original.entries` (the *list* is new) but
does not check that the *elements* of that list are new.

## Impact
- `filter_by_status` is a public API (re-exported in
  `epilogue/__init__.py:23` and `__all__`). A downstream consumer that treats
  the returned cycles as an independent copy and edits an entry in place will
  corrupt the original parsed cycles, with no error and no signal.
- The "never mutates the input" guarantee in the docstring is only true for
  the function's own behavior; it is false for any mutation of the returned
  structure, which is the natural reading of "NEW ... objects".
- Because the entries are shared, the same `Entry` object can appear in both
  the original cycle and a filtered result; any future code that annotates or
  rewrites entries (e.g. trimming, dedup, enrichment) will leak across the
  filter boundary.

## Suggestion
Decide the contract and make it true:
- If the returned structure should be independent (the natural reading of the
  docstring), copy the entries in `epilogue/render.py:173-178`, e.g.
  `matching = [replace(entry) for entry in cycle.entries if entry.status is status]`
  (or `dataclasses.replace` / a new `Entry(entry.description, entry.status)`),
  and update the docstring at `epilogue/render.py:155-158` and `43-44` to say
  the returned cycles contain NEW `Entry` objects.
- If aliasing is intentional, state it explicitly in the docstring ("the
  returned cycles share the input's `Entry` objects; do not mutate them") and
  add a test pinning `result[0].entries[0] is original.entries[0]`.
Add a test in `tests/test_render.py` asserting that mutating a returned entry
does NOT change the input (or, if aliasing is kept, asserting the shared
identity), so the contract is pinned by the gate.

Status: CLOSED (Cycle 10, PR #13). filter_by_status now returns fully independent Entry copies (dataclasses.replace) so mutating a returned entry never affects the input; docstring + module docstring updated; pinned by tests/test_render.py::test_filter_by_status_returns_new_entry_objects.
Issue: #66
