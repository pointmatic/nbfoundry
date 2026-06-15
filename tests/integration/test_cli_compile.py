# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Integration: `nbfoundry compile` builds a standalone artifact (Story G.c)."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from nbfoundry.cli import app

runner = CliRunner()

_NOTEBOOK = """\
import marimo

app = marimo.App()


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
"""


def _make_notebook_dir(base: Path) -> Path:
    src = base / "src"
    src.mkdir()
    (src / "notebook.py").write_text(_NOTEBOOK, encoding="utf-8")
    return src


def test_compile_emits_standalone_artifact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    src = _make_notebook_dir(tmp_path)
    out = tmp_path / "dist"

    result = runner.invoke(app, ["compile", str(src), "--out", str(out)])
    assert result.exit_code == 0, result.output

    assert (out / "notebook.py").is_file()
    assert (out / "launch.py").is_file()
    # standalone artifact carries venv/pip requirements, not a conda env file.
    assert (out / "requirements-base.txt").is_file()
    assert not (out / "environment.yml").exists()


def test_compile_refuses_existing_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    src = _make_notebook_dir(tmp_path)
    out = tmp_path / "dist"
    out.mkdir()  # pre-existing → refuse to overwrite
    result = runner.invoke(app, ["compile", str(src), "--out", str(out)])
    assert result.exit_code != 0
