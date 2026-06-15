# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Integration: `nbfoundry init` scaffolds each of the five templates (Story G.c)."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from nbfoundry.cli import app
from nbfoundry.errors import ExerciseError

runner = CliRunner()

TEMPLATES = [
    "data_exploration",
    "data_preparation",
    "model_experimentation",
    "model_optimization",
    "model_evaluation",
]


@pytest.mark.parametrize("template", TEMPLATES)
def test_init_scaffolds_each_template(
    template: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "demo", "--template", template])
    assert result.exit_code == 0, result.output
    proj = tmp_path / "demo"
    assert (proj / "notebook.py").is_file()
    # every scaffold ships at least the base requirements.
    assert (proj / "requirements-base.txt").is_file()


def test_init_default_template_is_data_exploration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "demo"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "demo" / "notebook.py").is_file()


def test_init_unknown_template_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "demo", "--template", "nope"])
    assert result.exit_code != 0
    assert isinstance(result.exception, ExerciseError)
    assert "unknown template" in result.exception.message


def test_init_existing_path_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "demo").mkdir()
    result = runner.invoke(app, ["init", "demo"])
    assert result.exit_code != 0
    assert isinstance(result.exception, ExerciseError)
