# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""End-to-end smoke for the scaffolded data_exploration template (Story F.h).

Scaffolds the framework-agnostic `data_exploration` template via `nbfoundry
init`, then runs the generated marimo notebook end-to-end and asserts the
load -> describe -> visualize flow produces its expected outputs (the synthetic
DataFrame, the `describe()` summary, the class-balance, and the matplotlib
figure). The template self-generates its synthetic dataset, so no external
input data is needed.

Env / marker decision (recorded at the F.h gate, 2026-06-14): this template is
framework-agnostic (pandas / scikit-learn / matplotlib / marimo + nbfoundry, no
torch/TF/Metal), so it runs in the **default `testenv`** with **no**
`@pytest.mark.hardware` marker — it executes on every `pyve test` run and in CI.
The light deps (numpy, pandas, matplotlib) live in `requirements-dev.txt`. This
is also the first smoke that invokes `nbfoundry init`, so it exercises the
packaged template + scaffolder surface.

Run procedure:

    pyve test tests/integration/test_e2e_template_data_exploration.py

Budget: under 60s on M-series silicon (tiny synthetic data, no acceleration).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import matplotlib
import pytest
from typer.testing import CliRunner

from nbfoundry.cli import app

# Headless backend so the figure cell never tries to open a GUI window.
matplotlib.use("Agg")

runner = CliRunner()


def _load_notebook(notebook_path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, notebook_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_data_exploration_template_runs_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init", "demo", "--template", "data_exploration"])
    assert result.exit_code == 0, result.output

    notebook = tmp_path / "demo" / "notebook.py"
    assert notebook.is_file()
    # Published-surface check: the scaffolder emits the stage requirements (F.f.4).
    assert (tmp_path / "demo" / "requirements-base.txt").is_file()

    module = _load_notebook(notebook, "demo_data_exploration_nb")
    outputs, defs = module.app.run()

    # Every cell produced an output (load, describe, class-balance md, viz, header).
    assert len(outputs) == 5

    # load cell: synthetic DataFrame with the documented shape and columns.
    df = defs["df"]
    assert df.shape == (200, 3)
    assert list(df.columns) == ["feature_a", "feature_b", "label"]

    # describe cell: a summary frame over all columns.
    summary = defs["summary"]
    assert "feature_a" in summary.columns

    # class-balance is computable over the label column (3 classes: 0,1,2).
    assert set(df["label"].unique()).issubset({0, 1, 2})

    # visualize cell: a matplotlib Figure was produced.
    fig = defs["fig"]
    assert fig.__class__.__name__ == "Figure"
    assert len(fig.axes) == 1
