# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""End-to-end smoke for the scaffolded data_preparation template (Story F.i).

Scaffolds the framework-agnostic `data_preparation` template via `nbfoundry
init`, then runs the generated marimo notebook end-to-end and asserts the
clean -> engineer -> split flow produces clean stratified train/test splits with
the expected shapes and class balance. The template self-generates its synthetic
dataset (and injects NaNs to demonstrate cleaning), so no external input data is
needed.

Env / marker decision (recorded at the F.h gate, 2026-06-14): framework-agnostic
template smokes run in the **default `testenv`** with **no**
`@pytest.mark.hardware` — they run on every `pyve test` and in CI. The light
deps (numpy, pandas, scikit-learn) live in `requirements-dev.txt`.

Run procedure:

    pyve test tests/integration/test_e2e_template_data_preparation.py

Budget: under 60s on M-series silicon (tiny synthetic data, no acceleration).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from typer.testing import CliRunner

from nbfoundry.cli import app

runner = CliRunner()


def _load_notebook(notebook_path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, notebook_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_data_preparation_template_runs_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init", "demo", "--template", "data_preparation"])
    assert result.exit_code == 0, result.output

    notebook = tmp_path / "demo" / "notebook.py"
    assert notebook.is_file()
    assert (tmp_path / "demo" / "requirements-base.txt").is_file()

    module = _load_notebook(notebook, "demo_data_preparation_nb")
    outputs, defs = module.app.run()

    # Every cell produced an output (header, load, clean, engineer, split, summary md).
    assert len(outputs) == 6

    # clean cell: the 10 injected NaN rows are dropped (200 -> 190); none remain.
    cleaned = defs["cleaned"]
    assert len(cleaned) == 190
    assert not cleaned.isna().any().any()

    # engineer cell: category one-hot expanded + interaction feature; label retained.
    feature_cols = defs["feature_cols"]
    assert "label" not in feature_cols
    assert "feature_a_x_b" in feature_cols
    assert {"category_alpha", "category_beta", "category_gamma"}.issubset(feature_cols)

    # split cell: 80/20 stratified split over the cleaned rows.
    X_train, X_test = defs["X_train"], defs["X_test"]
    y_train, y_test = defs["y_train"], defs["y_test"]
    assert len(X_train) + len(X_test) == 190
    assert len(X_test) == 38
    assert X_train.shape[1] == X_test.shape[1] == len(feature_cols)

    # stratify=y keeps both classes present in each split.
    assert set(y_train.unique()) == set(y_test.unique()) == {0, 1}
