# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Integration: `nbfoundry compile-exercise` end-to-end (Story I.e).

Drives the CLI through Typer's runner, then verifies the JSON it emits
conforms to the Option-C wire shape `{type, source, ref, title,
description, hints, environment, notebook_source}`.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from nbfoundry.cli import app

runner = CliRunner()


_OPTION_C_KEYS = {
    "type",
    "source",
    "ref",
    "title",
    "description",
    "hints",
    "environment",
    "notebook_source",
}


def test_compile_exercise_prints_option_c_json_to_stdout(tmp_base_dir: Path) -> None:
    yaml_path = tmp_base_dir / "valid_minimal.yaml"
    result = runner.invoke(app, ["compile-exercise", str(yaml_path)])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert set(payload.keys()) == _OPTION_C_KEYS
    assert payload["type"] == "exercise"
    assert payload["source"] == "nbfoundry"
    assert payload["notebook_source"].startswith("import marimo\n")


def test_compile_exercise_writes_out_file(tmp_base_dir: Path, tmp_path: Path) -> None:
    yaml_path = tmp_base_dir / "valid_minimal.yaml"
    out = tmp_path / "compiled.json"
    result = runner.invoke(app, ["compile-exercise", str(yaml_path), "--out", str(out)])
    assert result.exit_code == 0, result.output
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert set(payload.keys()) == _OPTION_C_KEYS
    assert "notebook_source" in payload


def test_compile_exercise_with_code_file_tree(tmp_base_dir: Path) -> None:
    """Tree fixture: exercise.yaml references `sections/*.py` via `code_file`.

    The base_dir is the tree root so `paths.resolve_under` correctly anchors
    the section file paths.
    """
    tree_base = tmp_base_dir / "tree"
    yaml_path = tree_base / "exercise.yaml"
    result = runner.invoke(
        app,
        ["compile-exercise", str(yaml_path), "--base-dir", str(tree_base)],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    # The contents of sections/load.py and sections/summarize.py should be
    # inlined into the generated notebook source.
    assert "pd.DataFrame" in payload["notebook_source"]
    assert "describe()" in payload["notebook_source"]
