# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from marimo._ast.parse import parse_notebook

from nbfoundry.errors import ExerciseError

ENTRY_FILENAME = "notebook.py"


@dataclass(frozen=True, slots=True)
class ParsedNotebook:
    path: Path
    serialization: Any  # marimo NotebookSerialization


def discover_entry(notebook_or_dir: Path) -> Path:
    if notebook_or_dir.is_file():
        return notebook_or_dir

    if not notebook_or_dir.is_dir():
        raise ExerciseError(
            file_path=notebook_or_dir,
            message=f"path is neither a notebook file nor a directory: {notebook_or_dir}",
        )

    conventional = notebook_or_dir / ENTRY_FILENAME
    if conventional.is_file():
        return conventional

    py_files = sorted(notebook_or_dir.glob("*.py"))
    if len(py_files) == 1:
        return py_files[0]

    raise ExerciseError(
        file_path=notebook_or_dir,
        message=(
            f"could not determine entry-point notebook in {notebook_or_dir}: "
            f"expected `{ENTRY_FILENAME}` or a single .py file"
        ),
    )


def parse_all(entry: Path) -> list[ParsedNotebook]:
    files = _collect_notebooks(entry)

    parsed: list[ParsedNotebook] = []
    failures: list[str] = []

    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except OSError as e:
            failures.append(f"{f}: could not read file ({e})")
            continue

        result = parse_notebook(text, filepath=str(f))
        if result is None or not getattr(result, "valid", True):
            for v in getattr(result, "violations", []) or []:
                line = getattr(v, "lineno", "?")
                desc = getattr(v, "description", "parse error")
                failures.append(f"{f}:{line}: {desc}")
            if result is None:
                failures.append(f"{f}: marimo could not parse the notebook")
            continue
        parsed.append(ParsedNotebook(path=f, serialization=result))

    if failures:
        raise ExerciseError(
            file_path=entry,
            message="failed to parse Marimo notebook(s):\n  " + "\n  ".join(failures),
        )

    return parsed


def _collect_notebooks(entry: Path) -> list[Path]:
    if entry.is_file():
        return [entry]
    if entry.is_dir():
        return sorted(p for p in entry.rglob("*.py") if p.is_file())
    raise ExerciseError(
        file_path=entry,
        message=f"path is neither a notebook file nor a directory: {entry}",
    )
