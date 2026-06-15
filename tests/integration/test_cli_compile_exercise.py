# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Integration: `nbfoundry compile-exercise` JSON to stdout / --out (Story G.c)."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from nbfoundry.cli import app

runner = CliRunner()


def test_compile_exercise_prints_json_to_stdout(tmp_base_dir: Path) -> None:
    yaml_path = tmp_base_dir / "valid_graded.yaml"
    result = runner.invoke(
        app, ["compile-exercise", str(yaml_path), "--base-dir", str(tmp_base_dir)]
    )
    assert result.exit_code == 0, result.output
    parsed = json.loads(result.stdout)
    assert parsed["type"] == "exercise"
    assert parsed["ref"] == "valid_graded.yaml"


def test_compile_exercise_writes_out_file(tmp_base_dir: Path, tmp_path: Path) -> None:
    yaml_path = tmp_base_dir / "valid_graded.yaml"
    out = tmp_path / "compiled.json"
    result = runner.invoke(
        app,
        ["compile-exercise", str(yaml_path), "--base-dir", str(tmp_base_dir), "--out", str(out)],
    )
    assert result.exit_code == 0, result.output
    assert out.is_file()
    parsed = json.loads(out.read_text(encoding="utf-8"))
    assert parsed["type"] == "exercise"


def test_compile_exercise_invalid_exits_nonzero(tmp_base_dir: Path) -> None:
    yaml_path = tmp_base_dir / "invalid_missing_title.yaml"
    result = runner.invoke(
        app, ["compile-exercise", str(yaml_path), "--base-dir", str(tmp_base_dir)]
    )
    assert result.exit_code != 0
