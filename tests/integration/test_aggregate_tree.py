# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Integration: notebook-tree exercise → single dict (Story G.c, FR-6)."""

from __future__ import annotations

from pathlib import Path

import pytest

from nbfoundry.compiler import compile_exercise
from nbfoundry.errors import ExerciseError


def test_tree_compiles_to_single_dict_with_inlined_notebooks(tmp_base_dir: Path) -> None:
    tree_base = tmp_base_dir / "tree"
    compiled = compile_exercise(Path("exercise.yaml"), tree_base)
    assert compiled["type"] == "exercise"
    assert len(compiled["sections"]) == 2
    # tree-internal notebooks are inlined into their sections.
    assert "data = [1, 2, 3]" in compiled["sections"][0]["code"]
    assert "total = sum(data)" in compiled["sections"][1]["code"]


def test_tree_external_reference_rejected(tmp_path: Path) -> None:
    # A real file outside the tree, plus a tree whose section escapes to it.
    (tmp_path / "secret.py").write_text("import marimo\napp = marimo.App()\n", encoding="utf-8")
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "exercise.yaml").write_text(
        "title: T\n"
        "description: d\n"
        "sections:\n"
        "  - title: S\n    description: b\n    code_file: ../secret.py\n",
        encoding="utf-8",
    )
    with pytest.raises(ExerciseError) as ei:
        compile_exercise(Path("exercise.yaml"), tree)
    assert "escapes base directory" in ei.value.message
