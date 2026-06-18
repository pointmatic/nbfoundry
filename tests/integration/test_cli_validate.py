# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Integration: `nbfoundry validate` CLI exit codes (Story I.e)."""

from __future__ import annotations

import textwrap
from pathlib import Path

from typer.testing import CliRunner

from nbfoundry.cli import app

runner = CliRunner()


def test_validate_valid_definition_exits_zero_silent(tmp_base_dir: Path) -> None:
    yaml_path = tmp_base_dir / "valid_minimal.yaml"
    result = runner.invoke(app, ["validate", str(yaml_path)])
    assert result.exit_code == 0
    assert result.output == ""


def test_validate_invalid_definition_exits_one_with_errors(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        textwrap.dedent(
            """\
            title: T
            description: "d"
            sections:
              - title: s
                description: "d"
                code: "x = 1"
                editable: true
            """
        ),
        encoding="utf-8",
    )
    result = runner.invoke(app, ["validate", str(bad)])
    assert result.exit_code == 1
    assert result.output  # error lines printed to stdout
