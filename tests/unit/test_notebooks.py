# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Notebook discovery + parse unit sweep (Story G.e coverage gap-fill)."""

from __future__ import annotations

from pathlib import Path

import pytest

from nbfoundry import notebooks
from nbfoundry.errors import ExerciseError

_VALID = """\
import marimo

app = marimo.App()


@app.cell
def _():
    return
"""


def _nb(path: Path, text: str = _VALID) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# discover_entry
# --------------------------------------------------------------------------- #


def test_discover_entry_returns_file_directly(tmp_path: Path) -> None:
    f = _nb(tmp_path / "thing.py")
    assert notebooks.discover_entry(f) == f


def test_discover_entry_prefers_conventional_notebook_py(tmp_path: Path) -> None:
    _nb(tmp_path / "notebook.py")
    _nb(tmp_path / "other.py")
    assert notebooks.discover_entry(tmp_path) == tmp_path / "notebook.py"


def test_discover_entry_single_py_file(tmp_path: Path) -> None:
    _nb(tmp_path / "only.py")
    assert notebooks.discover_entry(tmp_path) == tmp_path / "only.py"


def test_discover_entry_ambiguous_dir_raises(tmp_path: Path) -> None:
    _nb(tmp_path / "a.py")
    _nb(tmp_path / "b.py")
    with pytest.raises(ExerciseError, match="could not determine entry-point"):
        notebooks.discover_entry(tmp_path)


def test_discover_entry_nonexistent_raises(tmp_path: Path) -> None:
    with pytest.raises(ExerciseError, match="neither a notebook file nor a directory"):
        notebooks.discover_entry(tmp_path / "nope")


# --------------------------------------------------------------------------- #
# parse_all
# --------------------------------------------------------------------------- #


def test_parse_all_single_file(tmp_path: Path) -> None:
    f = _nb(tmp_path / "notebook.py")
    parsed = notebooks.parse_all(f)
    assert len(parsed) == 1
    assert parsed[0].path == f


def test_parse_all_directory_collects_all(tmp_path: Path) -> None:
    _nb(tmp_path / "notebook.py")
    _nb(tmp_path / "extra.py")
    parsed = notebooks.parse_all(tmp_path)
    assert {p.path.name for p in parsed} == {"notebook.py", "extra.py"}


def test_parse_all_syntax_error_raises(tmp_path: Path) -> None:
    _nb(tmp_path / "bad.py", "def (oops this is not valid python\n")
    with pytest.raises(ExerciseError, match="failed to parse Marimo notebook"):
        notebooks.parse_all(tmp_path / "bad.py")


def test_parse_all_nonexistent_path_raises(tmp_path: Path) -> None:
    with pytest.raises(ExerciseError, match="neither a notebook file nor a directory"):
        notebooks.parse_all(tmp_path / "nope")
