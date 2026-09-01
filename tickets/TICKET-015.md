# TICKET-015: `epilogue/__init__.py` docstring is stale — claims only the data model ships

## Title
The package docstring in `epilogue/__init__.py` is inaccurate: it states the
bootstrap cycle "ships only the data model" and that the "parse-to-render-to-CLI
capability is a later build cycle," but the CLI shell already exists.

## Evidence
- `epilogue/__init__.py:3-4` — "This bootstrap cycle ships only the data model.
  The parse-to-render-to-CLI capability is a later build cycle."
- `epilogue/cli.py` and `epilogue/__main__.py` both exist (added in Cycle 2,
  commit `3dde27a`, PR #2) and provide a runnable `main(argv) -> int` and a
  `python -m epilogue` entry point.
- `README.md` "Structure" section lists `cli.py` and `__main__.py` as shipped
  modules, contradicting the `__init__.py` claim that only the data model ships.
- `git log --oneline` shows `3dde27a feat: add runnable CLI shell (...) (#2)`
  after the bootstrap commit, confirming the CLI is no longer "a later build
  cycle."

## Impact
- A reader of the package docstring gets a false picture of what is implemented;
  the docstring understates the current state.
- The audit rule "documentation must be accurate" is violated: the docstring
  describes a prior cycle, not the current one.
- It muddies the boundary between what is done (CLI shell) and what is pending
  (parse-to-render), which is exactly the distinction the mission cares about.

## Suggestion
Update the `epilogue/__init__.py` module docstring to reflect the current state:
the data model and the CLI shell are shipped; the *parse-to-render* capability
is the pending build phase. Keep the public-API list accurate (currently
`Cycle`, `Entry`, `MergeStatus`, `__version__`). Do not over-claim: the parser
and renderer are still absent (TICKET-011), so the docstring should say the
parse-to-render capability is pending, not that the CLI is.

---
Status: CLOSED (Cycle 3, PR #3, merged 6bc0053)
