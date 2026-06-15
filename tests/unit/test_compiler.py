# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Compiler core unit sweep (Story G.b) — compile_exercise happy path + edges."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from nbfoundry.compiler import compile_exercise
from nbfoundry.errors import ExerciseError


def _write(base: Path, name: str, text: str) -> Path:
    p = base / name
    p.write_text(textwrap.dedent(text), encoding="utf-8")
    return p


def test_compile_happy_path_wire_shape(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "ex.yaml",
        """\
        title: T
        description: hello
        sections:
          - title: S
            description: body
            code: |
              x = 1
        """,
    )
    out = compile_exercise(Path("ex.yaml"), tmp_path)
    assert out["type"] == "exercise"
    assert out["source"] == "nbfoundry"
    assert out["status"] == "ready"
    assert out["ref"] == "ex.yaml"
    assert out["title"] == "T"
    assert out["sections"][0]["code"] == "x = 1\n"
    assert out["assets"] == []
    assert out["submission"] is None and out["environment"] is None


def test_description_is_markdown_rendered(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "ex.yaml",
        """\
        title: T
        description: '**bold**'
        sections:
          - title: S
            description: '*em*'
            code: x = 1
        """,
    )
    out = compile_exercise(Path("ex.yaml"), tmp_path)
    assert out["instructions"] == "<p><strong>bold</strong></p>"
    assert out["sections"][0]["description"] == "<p><em>em</em></p>"


def test_code_file_is_inlined(tmp_path: Path) -> None:
    _write(tmp_path, "snippet.py", "import marimo\napp = marimo.App()\n")
    _write(
        tmp_path,
        "ex.yaml",
        """\
        title: T
        description: d
        sections:
          - title: S
            description: b
            code_file: snippet.py
        """,
    )
    out = compile_exercise(Path("ex.yaml"), tmp_path)
    assert "import marimo" in out["sections"][0]["code"]


def test_section_error_carries_section_index(tmp_path: Path) -> None:
    # second section references a path that escapes base_dir.
    _write(
        tmp_path,
        "ex.yaml",
        """\
        title: T
        description: d
        sections:
          - title: S0
            description: b
            code: x = 1
          - title: S1
            description: b
            code_file: ../escape.py
        """,
    )
    with pytest.raises(ExerciseError) as ei:
        compile_exercise(Path("ex.yaml"), tmp_path)
    assert "sections[1].code_file" in ei.value.message


def test_image_asset_enumerated_in_output(tmp_path: Path) -> None:
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "p.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    _write(
        tmp_path,
        "ex.yaml",
        """\
        title: T
        description: d
        sections:
          - title: S
            description: b
            code: x = 1
        expected_outputs:
          - description: o
            type: image
            path: assets/p.png
            alt: a
        """,
    )
    out = compile_exercise(Path("ex.yaml"), tmp_path)
    assert out["assets"] == ["assets/p.png"]
    assert out["expected_outputs"][0]["type"] == "image"


def test_compile_raises_first_error_on_invalid(tmp_path: Path) -> None:
    _write(tmp_path, "ex.yaml", "title: T\ndescription: d\nsections: []\n")
    with pytest.raises(ExerciseError):
        compile_exercise(Path("ex.yaml"), tmp_path)
