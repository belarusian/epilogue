# TICKET-053: README documents an impossible "project key omitted when --project not given"

## Title
The README's "Machine-readable output" section states that the `project` key is
omitted "when `--project` is not given". But `--project` is a **required**
argument in the CLI, so it can never be omitted — the documented behavior is
unreachable through the CLI. The `project=None` branch that the sentence
describes only exists in the library functions `render` / `render_json`, which
the CLI never calls with `project=None`.

## Evidence
`epilogue/cli.py:52-57` — `--project` is required:
    parser.add_argument(
        "--project",
        type=str,
        required=True,
        help="Name of the project the cycle log belongs to.",
    )

Reproduced: omitting `--project` is a usage error, exit `2`:
    $ python3 -m epilogue --from 1 --to 1 --log good.md
    epilogue: error: the following arguments are required: --project
    EXIT=2

The CLI always passes a real project name to the renderers
(`cli.py:154` `render_json(selected, project=args.project)` and
`cli.py:156` `render(selected, project=args.project)`), so the `project is not
None` branch in `render.py:79` / `render.py:144` is always taken from the CLI.

README lines 257-258:
    The `project` key is omitted entirely when `--project` is not given (the
    literal string `"None"` is never emitted).

## Impact
- A reader of the README believes they can run the CLI without `--project` and
  get a `project`-less JSON document. They cannot; they get a usage error.
- The sentence describes a library-level behavior (`render_json(..., project=None)`)
  as if it were a CLI behavior, conflating the two surfaces.
- The "literal string `"None"` is never emitted" reassurance is accurate but
  attached to a premise (omitting `--project`) that the CLI forbids.

## Suggestion
Either (a) make the README sentence explicitly about the library API
(`render_json(cycles, project=None)` omits the key when `project` is `None`),
clearly separating it from the CLI where `--project` is required; or (b) if the
intent is that the CLI should allow omitting `--project`, make `--project`
optional (`required=False, default=None`) and add a test. Pick one and align the
docs with the code.

**Status: CLOSED (Cycle 23, PR #26).**

Issue: #86
