# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Integration: valid_graded.yaml → golden JSON byte-for-byte (Story G.c, TR-2/QR-5)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from nbfoundry.cli import app
from nbfoundry.compiler import compile_exercise

runner = CliRunner()


def _serialize(obj: Any) -> str:
    return json.dumps(obj, sort_keys=False, ensure_ascii=False, separators=(",", ": "), indent=2)


def test_library_compile_matches_golden_dict(
    tmp_base_dir: Path, sample_yaml: Path, golden_dict: dict[str, Any]
) -> None:
    assert compile_exercise(sample_yaml, tmp_base_dir) == golden_dict


def test_cli_out_is_byte_for_byte_golden(
    tmp_base_dir: Path, fixtures_dir: Path, tmp_path: Path
) -> None:
    out = tmp_path / "out.json"
    result = runner.invoke(
        app,
        [
            "compile-exercise",
            str(tmp_base_dir / "valid_graded.yaml"),
            "--base-dir",
            str(tmp_base_dir),
            "--out",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    golden_text = (fixtures_dir / "golden" / "valid_graded.json").read_text(encoding="utf-8")
    assert out.read_text(encoding="utf-8") == golden_text


def test_golden_serialization_roundtrips(
    tmp_base_dir: Path, sample_yaml: Path, golden_dict: dict[str, Any]
) -> None:
    compiled = compile_exercise(sample_yaml, tmp_base_dir)
    assert _serialize(compiled) == _serialize(golden_dict)
