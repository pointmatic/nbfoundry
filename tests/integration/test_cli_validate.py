# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Integration: `nbfoundry validate` exit codes (Story G.c)."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from nbfoundry.cli import app

runner = CliRunner()


def test_validate_valid_exits_zero_no_output(tmp_base_dir: Path) -> None:
    yaml_path = tmp_base_dir / "valid_minimal.yaml"
    result = runner.invoke(app, ["validate", str(yaml_path), "--base-dir", str(tmp_base_dir)])
    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == ""


def test_validate_invalid_exits_one_with_errors(tmp_base_dir: Path) -> None:
    yaml_path = tmp_base_dir / "invalid_duplicate_field_name.yaml"
    result = runner.invoke(app, ["validate", str(yaml_path), "--base-dir", str(tmp_base_dir)])
    assert result.exit_code == 1
    assert result.stdout.strip() != ""


def test_validate_reports_all_errors(tmp_base_dir: Path) -> None:
    # craft a two-error YAML in the writable base
    (tmp_base_dir / "two_errors.yaml").write_text(
        "title: T\n"
        "description: d\n"
        "sections:\n"
        "  - title: S0\n    description: b\n    code_file: ../a.py\n"
        "  - title: S1\n    description: b\n    code_file: ../b.py\n",
        encoding="utf-8",
    )
    result = runner.invoke(
        app, ["validate", str(tmp_base_dir / "two_errors.yaml"), "--base-dir", str(tmp_base_dir)]
    )
    assert result.exit_code == 1
    lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
    assert len(lines) == 2
