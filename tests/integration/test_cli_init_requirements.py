# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""`nbfoundry init` emits the stage-appropriate venv/pip requirements (Story F.f.4).

The conda bundled payload (`templates/environment.yml`) is gone; each scaffolded
project now ships per-stage pip requirements:

    data_exploration / data_preparation        -> requirements-base.txt
    model_experimentation / _optimization / _evaluation -> requirements-torch.txt

`requirements-torch.txt` opens with `-r requirements-base.txt`, so the base file
must ship alongside it. No `environment.yml`, no conda, anywhere.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from nbfoundry.cli import app

runner = CliRunner()

# model_evaluation is sklearn-based (F.j), so it maps to base, not torch.
BASE_STAGES = ["data_exploration", "data_preparation", "model_evaluation"]
TORCH_STAGES = ["model_experimentation", "model_optimization"]


@pytest.mark.parametrize("stage", BASE_STAGES)
def test_data_stage_emits_base_requirements_only(
    stage: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "demo", "--template", stage])
    assert result.exit_code == 0, result.output
    proj = tmp_path / "demo"
    assert (proj / "requirements-base.txt").is_file()
    assert not (proj / "requirements-torch.txt").exists()
    assert not (proj / "requirements-tf.txt").exists()
    assert not (proj / "environment.yml").exists()


@pytest.mark.parametrize("stage", TORCH_STAGES)
def test_model_stage_emits_torch_requirements_with_base(
    stage: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "demo", "--template", stage])
    assert result.exit_code == 0, result.output
    proj = tmp_path / "demo"
    assert (proj / "requirements-torch.txt").is_file()
    # torch requirements include the base via `-r`, so base must ship too.
    assert (proj / "requirements-base.txt").is_file()
    assert not (proj / "environment.yml").exists()


def test_no_template_ships_a_conda_environment_yml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    for i, stage in enumerate(BASE_STAGES + TORCH_STAGES):
        result = runner.invoke(app, ["init", f"d{i}", "--template", stage])
        assert result.exit_code == 0, result.output
        assert not (tmp_path / f"d{i}" / "environment.yml").exists()
