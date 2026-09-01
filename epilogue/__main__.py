"""Entry point for ``python -m epilogue``.

Delegates to :func:`epilogue.cli.main` and exits with its return code.
"""

from __future__ import annotations

import sys

from epilogue.cli import main

if __name__ == "__main__":
    sys.exit(main())
