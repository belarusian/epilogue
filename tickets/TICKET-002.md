# TICKET-002: No `pyproject.toml` — package is not importable, typed, or lintable

## Title
Missing `pyproject.toml` at repo root; no build system, entry point, or tool configuration.

## Evidence
- `ls -la` at repo root shows no `pyproject.toml`, `setup.py`, `setup.cfg`, or `tox.ini`.
- No `[project]` metadata, no `[project.scripts]` entry point for the `epilogue` CLI command.
- No `[tool.ruff]`, `[tool.mypy]`, or `[tool.pytest.ini_options]` sections anywhere in the repo.
- The README states "stdlib only" and "full pytest suite; CI green on push" but no configuration exists to enforce any of this.

## Impact
- `pip install -e .` will fail; the package cannot be installed in editable mode for development.
- `ruff check .` and `mypy epilogue/` have no project-level configuration (line length, strictness, Python target version).
- CI (TICKET-004) has nothing to configure; the gate cannot be defined.
- The `epilogue` console-script entry point does not exist, so users must rely on `python -m epilogue`.

## Suggestion
Create `pyproject.toml` with at minimum: