# TICKET-054: Text output ends with a double trailing newline; JSON ends with a single one
**Status: CLOSED (Cycle 21, PR #24).** FIXED: both documented output formats now end with exactly one trailing newline. In `epilogue/cli.py` the final `print(out)` was replaced with `sys.stdout.write(out.rstrip("\n") + "\n")`, which strips any trailing newlines and appends exactly one, so text and json are byte-consistent. Note: the ticket's premise that `render()` returns a string ending in *exactly one* newline was incorrect — for non-empty input `render()` ends in two newlines (a trailing blank line), so the ticket's literal suggestion (`sys.stdout.write(out)` for text) would have left text ending in `\n\n`. The fix normalizes in the CLI instead, leaving the `render()`/`render_json()` library contract untouched (`render([]) == "No cycles.\n"` and the docstring are unchanged). Pinned by `tests/test_cli.py::test_text_format_ends_with_exactly_one_trailing_newline` and `::test_json_format_ends_with_exactly_one_trailing_newline` (byte-exact: `out.endswith("\n")` and `not out.endswith("\n\n")` for both formats; the text test fails against the pre-fix code).


## Title
The CLI prints its output with `print(out)` (`cli.py:157`). For the `text`
format, `render()` already returns a string that ends in a newline
(`render.py:106` `return "\n".join(lines) + "\n"`), so `print` appends a second
newline and the text output ends with **two** trailing newlines. For the `json`
format, `render_json()` returns `json.dumps(doc)` with no trailing newline
(`render.py:152`), so `print` appends exactly one. The two formats are
inconsistent in their trailing whitespace.

## Evidence
`epilogue/render.py:106`:
    return "\n".join(lines) + "\n"
`epilogue/render.py:152`:
    return json.dumps(doc)
`epilogue/cli.py:154-157`:
    if args.output_format == "json":
        out = render_json(selected, project=args.project)
    else:
        out = render(selected, project=args.project)
    print(out)

Reproduced against the shipped code (Python 3.10), byte-level (`od -c`):

text format stdout ends:
    ... m a d e   t h e   g a t e   g r e e n \n \n \n
    (three newlines: one from the last entry line, one from render's `+ "\n"`,
     one from `print`)

json format stdout ends:
    ... } ] } ] } \n
    (a single newline, from `print` only)

## Impact
- A consumer that captures stdout and compares it byte-for-byte (or strips
  exactly one trailing newline) gets a different result depending on `--format`.
- The extra blank line at the end of text output is a cosmetic inconsistency
  with the JSON output and with the README's own examples, which show the text
  changelog ending after the last entry (single trailing newline).
- It is a small but real divergence between the two documented output formats.

## Suggestion
Make the trailing newline consistent. The simplest fix is to print without an
extra newline for the text path, e.g. `sys.stdout.write(out)` for text (which
already ends in `\n`) and `print(out)` for json — or, more uniformly,
`sys.stdout.write(out + "\n")` for both after normalizing `render` to not add
its own trailing newline. Whichever is chosen, pin it with a byte-exact test for
both formats (see TICKET-055).

Issue: #87
