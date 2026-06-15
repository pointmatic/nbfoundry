# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""`nbfoundry compile` emits venv/pip requirements, not conda (Story F.f.4).

The standalone artifact no longer carries an `environment.yml`. It preserves any
`requirements*.txt` the source ships, and — when the source carries none — falls
back to the agnostic `requirements-base.txt` so the artifact is always
installable with `pip install -r`. When a stage file that `-r`-includes the base
is present, the base is guaranteed alongside it.
"""

from __future__ import annotations

from pathlib import Path

from nbfoundry.standalone import compile as compile_standalone

_MINIMAL_NOTEBOOK = """\
import marimo

app = marimo.App()


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
"""


def _write_notebook(d: Path) -> None:
    (d / "notebook.py").write_text(_MINIMAL_NOTEBOOK, encoding="utf-8")


def test_compile_with_no_requirements_falls_back_to_base(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    _write_notebook(src)

    out = compile_standalone(src, tmp_path / "dist")

    assert (out / "requirements-base.txt").is_file()
    assert not (out / "environment.yml").exists()
    assert (out / "launch.py").is_file()


def test_compile_preserves_stage_requirements_and_ensures_base(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    _write_notebook(src)
    (src / "requirements-torch.txt").write_text(
        "-r requirements-base.txt\ntorch>=2.5\n", encoding="utf-8"
    )

    out = compile_standalone(src, tmp_path / "dist")

    assert (out / "requirements-torch.txt").is_file()
    # base must ship because the torch file `-r`-includes it.
    assert (out / "requirements-base.txt").is_file()
    assert not (out / "environment.yml").exists()
