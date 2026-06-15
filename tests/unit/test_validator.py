# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Validator unit sweep (Story G.b) — validate_exercise collect-all + short-circuit.

`validate_exercise` lives in `compiler.py` (no separate validator module); these
tests exercise its FR-4 collect-all semantics and FR-5 short-circuit behavior.
"""

from __future__ import annotations

from pathlib import Path

from nbfoundry.compiler import validate_exercise


def _write(base: Path, name: str, text: str) -> None:
    (base / name).write_text(text, encoding="utf-8")


def test_valid_input_returns_empty_list(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "ex.yaml",
        "title: T\ndescription: d\nsections:\n  - title: S\n    description: b\n    code: x = 1\n",
    )
    assert validate_exercise(Path("ex.yaml"), tmp_path) == []


def test_collects_multiple_errors(tmp_path: Path) -> None:
    # Two sections each reference an escaping code_file → two accumulated errors.
    _write(
        tmp_path,
        "ex.yaml",
        (
            "title: T\ndescription: d\nsections:\n"
            "  - title: S0\n    description: b\n    code_file: ../a.py\n"
            "  - title: S1\n    description: b\n    code_file: ../b.py\n"
        ),
    )
    errors = validate_exercise(Path("ex.yaml"), tmp_path)
    assert len(errors) == 2
    assert any("sections[0]" in e for e in errors)
    assert any("sections[1]" in e for e in errors)


def test_yaml_parse_failure_short_circuits(tmp_path: Path) -> None:
    _write(tmp_path, "ex.yaml", "title: T\ndescription: '[unterminated\n")
    errors = validate_exercise(Path("ex.yaml"), tmp_path)
    assert len(errors) == 1
    assert "YAML parse error" in errors[0]


def test_non_mapping_top_level_short_circuits(tmp_path: Path) -> None:
    _write(tmp_path, "ex.yaml", "- a\n- b\n")
    errors = validate_exercise(Path("ex.yaml"), tmp_path)
    assert len(errors) == 1
    assert "must be a mapping" in errors[0]


def test_missing_yaml_file_reports_path_error(tmp_path: Path) -> None:
    errors = validate_exercise(Path("nope.yaml"), tmp_path)
    assert len(errors) == 1
    assert "does not exist" in errors[0]


def test_schema_failure_short_circuits_before_pipeline(tmp_path: Path) -> None:
    # An invalid schema (empty sections) is returned from the Pydantic stage and
    # the asset/codefile pipeline is not reached.
    _write(tmp_path, "ex.yaml", "title: T\ndescription: d\nsections: []\n")
    errors = validate_exercise(Path("ex.yaml"), tmp_path)
    assert errors  # at least one schema error
