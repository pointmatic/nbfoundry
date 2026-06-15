# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""End-to-end smoke for the scaffolded model_evaluation template (Story F.j).

Scaffolds the `model_evaluation` template via `nbfoundry init`, then runs the
generated marimo notebook end-to-end and asserts the held-out evaluation ->
confusion matrix -> calibration flow produces its expected artifacts (a fitted
scikit-learn model, a confusion matrix, a rendered confusion-matrix figure, and
a calibration/reliability figure). The template self-generates synthetic data
and self-fits the model, so no external model or holdout fixture is needed.

Env / marker decision (recorded at the F.j gate, 2026-06-14): the
model_evaluation template was reshaped to a **scikit-learn** example (not
torch) — evaluation is framework-agnostic, so its mechanics don't need a deep
learning / Metal implementation. It therefore runs in the **default `testenv`**
with **no** `@pytest.mark.hardware`, on every `pyve test` and in CI; its deps
(`numpy` / `pandas` / `scikit-learn` / `matplotlib`) are in `requirements-dev.txt`
and the shipped stage requirements is `requirements-base.txt` (no torch).

Run procedure:

    pyve test tests/integration/test_e2e_template_model_evaluation.py

Budget: under 60s on M-series silicon (tiny synthetic data, no acceleration).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import matplotlib
import pytest
from typer.testing import CliRunner

from nbfoundry.cli import app

matplotlib.use("Agg")

runner = CliRunner()


def _load_notebook(notebook_path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, notebook_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_model_evaluation_template_runs_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init", "demo", "--template", "model_evaluation"])
    assert result.exit_code == 0, result.output

    notebook = tmp_path / "demo" / "notebook.py"
    assert notebook.is_file()
    # model_evaluation is sklearn-based → ships the base requirements (F.j), not torch.
    assert (tmp_path / "demo" / "requirements-base.txt").is_file()
    assert not (tmp_path / "demo" / "requirements-torch.txt").exists()

    module = _load_notebook(notebook, "demo_model_evaluation_nb")
    outputs, defs = module.app.run()

    # Every cell produced an output (header, data, fit, predict, report, cm, cal, final).
    assert len(outputs) == 8

    # Framework-agnostic example: a scikit-learn estimator, no torch anywhere.
    assert type(defs["model"]).__name__ == "LogisticRegression"
    assert not any("torch" in k for k in defs)

    # predict cell: held-out predictions over the 25% test split (1024 → 256).
    assert len(defs["y_true"]) == 256
    assert len(defs["y_pred"]) == 256

    # confusion-matrix cell: a 2x2 matrix covering all held-out rows + a Figure.
    cm = defs["cm"]
    assert cm.shape == (2, 2)
    assert cm.sum() == 256
    assert defs["fig_cm"].__class__.__name__ == "Figure"

    # calibration cell: a reliability-diagram Figure was produced.
    assert defs["fig_cal"].__class__.__name__ == "Figure"

    # final-report cell: a sane accuracy on the easily-separable synthetic task.
    assert 0.5 <= float(defs["accuracy"]) <= 1.0
