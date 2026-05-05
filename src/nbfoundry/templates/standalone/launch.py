# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Launch the standalone Marimo notebook artifact emitted by `nbfoundry compile`.

Runs `marimo edit <entry>` against the entry-point notebook in the same
directory. The entry point is `notebook.py` if present; otherwise the lone
`.py` file other than this launcher.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ENTRY_FILENAME = "notebook.py"


def _find_entry(here: Path) -> Path:
    conventional = here / ENTRY_FILENAME
    if conventional.is_file():
        return conventional
    candidates = sorted(p for p in here.glob("*.py") if p.name != "launch.py")
    if len(candidates) == 1:
        return candidates[0]
    raise SystemExit(
        f"could not determine entry-point notebook in {here}: "
        f"expected `{ENTRY_FILENAME}` or a single .py file other than launch.py"
    )


def main() -> None:
    here = Path(__file__).resolve().parent
    entry = _find_entry(here)
    subprocess.run([sys.executable, "-m", "marimo", "edit", str(entry)], check=True)


if __name__ == "__main__":
    main()
