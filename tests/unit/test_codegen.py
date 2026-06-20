# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Option-C codegen TDD smoke (Story I.c).

Small focused tests for `nbfoundry.codegen.generate` and the
`ensure_marimo_pinned` helper. The authoritative codegen sweep (including
the marimo-loads-the-generated-module integration smoke) lives in Story
I.e; this file just covers the red-green-refactor cycle for I.c itself.
"""

from __future__ import annotations

import ast
from importlib.metadata import version as _pkg_version
from pathlib import Path

import pytest

from nbfoundry import codegen
from nbfoundry.errors import ExerciseError
from nbfoundry.schema import EnvironmentModel, ExerciseDefinition, SectionModel


def _section(**over: object) -> SectionModel:
    base = {
        "title": "Detect device",
        "description": "Pick MPS if available, else CPU.",
        "code": "import torch\ndevice = torch.device('cpu')\n",
    }
    base.update(over)
    return SectionModel.model_validate(base)


def _defn(**over: object) -> ExerciseDefinition:
    base: dict[str, object] = {
        "title": "MPS smoke",
        "description": "Confirm torch sees Apple Metal.",
        "sections": [
            {
                "title": "Detect device",
                "description": "Pick MPS if available, else CPU.",
                "code": "import torch\ndevice = torch.device('cpu')\n",
            }
        ],
    }
    base.update(over)
    return ExerciseDefinition.model_validate(base)


# --------------------------------------------------------------------------- #
# generate()
# --------------------------------------------------------------------------- #


def test_generate_produces_valid_python_module(tmp_path: Path) -> None:
    src = codegen.generate(_defn(), base_dir=tmp_path)
    ast.parse(src)  # raises if not valid


def test_generate_shape_matches_spike_pattern(tmp_path: Path) -> None:
    src = codegen.generate(_defn(), base_dir=tmp_path)
    assert src.startswith("import marimo\n")
    assert "app = marimo.App()\n" in src
    assert "@app.cell\n" in src
    assert 'if __name__ == "__main__":\n    app.run()\n' in src


def test_generate_emits_framework_import_as_text_inside_code_cell(tmp_path: Path) -> None:
    src = codegen.generate(_defn(), base_dir=tmp_path)
    # The author's code contains `import torch`; codegen must emit it as
    # source text inside a code cell, not import it at build time.
    assert "import torch" in src


def test_generate_is_deterministic(tmp_path: Path) -> None:
    defn = _defn()
    a = codegen.generate(defn, base_dir=tmp_path)
    b = codegen.generate(defn, base_dir=tmp_path)
    assert a == b


def test_generated_with_matches_installed_marimo(tmp_path: Path) -> None:
    src = codegen.generate(_defn(), base_dir=tmp_path)
    expected = _pkg_version("marimo")
    assert f"__generated_with = {expected!r}" in src


def test_generate_inlines_code_file_relative_to_base_dir(tmp_path: Path) -> None:
    code_path = tmp_path / "section.py"
    code_path.write_text("y = 42\n", encoding="utf-8")
    defn = _defn(
        sections=[
            {
                "title": "From file",
                "description": "Body lives in section.py.",
                "code_file": "section.py",
            }
        ]
    )
    src = codegen.generate(defn, base_dir=tmp_path)
    assert "y = 42" in src


def test_generate_rejects_code_file_path_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.py"
    outside.write_text("y = 1\n", encoding="utf-8")
    try:
        defn = _defn(
            sections=[
                {
                    "title": "Escape attempt",
                    "description": "Tries to escape base_dir.",
                    "code_file": "../outside.py",
                }
            ]
        )
        with pytest.raises(ExerciseError):
            codegen.generate(defn, base_dir=tmp_path)
    finally:
        outside.unlink(missing_ok=True)


def test_generate_raises_on_missing_code_file(tmp_path: Path) -> None:
    defn = _defn(
        sections=[
            {
                "title": "Missing",
                "description": "References a nonexistent file.",
                "code_file": "does-not-exist.py",
            }
        ]
    )
    with pytest.raises(ExerciseError):
        codegen.generate(defn, base_dir=tmp_path)


def test_generate_emits_one_markdown_and_one_code_cell_per_section(tmp_path: Path) -> None:
    defn = _defn(
        sections=[
            {"title": "A", "description": "Da.", "code": "a = 1\n"},
            {"title": "B", "description": "Db.", "code": "b = 2\n"},
        ]
    )
    src = codegen.generate(defn, base_dir=tmp_path)
    # The banner/header cell is hidden (Story I.h), so the bare `@app.cell`
    # decorators are: 2 sections * (1 md cell + 1 code cell) = 4.
    assert src.count("@app.cell\n") == 4


# --------------------------------------------------------------------------- #
# hide_code (Story I.g) + hidden banner (Story I.h)
# --------------------------------------------------------------------------- #


def test_generate_banner_cell_has_hidden_code(tmp_path: Path) -> None:
    # Story I.h: the banner/header cell is pure presentation — its code
    # (`import marimo as mo` + `mo.md(...)`) must be hidden so the learner sees
    # the rendered title+description, not the boilerplate.
    src = codegen.generate(_defn(), base_dir=tmp_path)
    assert "@app.cell(hide_code=True)\ndef _():\n    import marimo as mo\n" in src


def test_generate_unflagged_section_leaves_only_banner_hidden(tmp_path: Path) -> None:
    # With no section flagged, the lone hidden cell is the banner (Story I.h);
    # an unflagged section's code cell stays bare (Story I.g default).
    src = codegen.generate(_defn(), base_dir=tmp_path)
    assert src.count("@app.cell(hide_code=True)\n") == 1


def test_generate_emits_hide_code_decorator_when_set(tmp_path: Path) -> None:
    defn = _defn(
        sections=[
            {
                "title": "Hidden",
                "description": "Output only.",
                "code": "x = 1\n",
                "hide_code": True,
            }
        ]
    )
    src = codegen.generate(defn, base_dir=tmp_path)
    assert "@app.cell(hide_code=True)\n" in src
    ast.parse(src)  # decorator-with-kwarg must stay valid Python


def test_generate_hide_code_only_affects_flagged_section(tmp_path: Path) -> None:
    defn = _defn(
        sections=[
            {"title": "Shown", "description": "Visible.", "code": "a = 1\n"},
            {
                "title": "Hidden",
                "description": "Hidden.",
                "code": "b = 2\n",
                "hide_code": True,
            },
        ]
    )
    src = codegen.generate(defn, base_dir=tmp_path)
    # Two hidden cells: the banner (Story I.h) + the one flagged section.
    assert src.count("@app.cell(hide_code=True)\n") == 2
    # Bare cells: 2 md cells + the visible section's code cell = 3 (the banner
    # is no longer bare).
    assert src.count("@app.cell\n") == 3


# --------------------------------------------------------------------------- #
# ensure_marimo_pinned()
# --------------------------------------------------------------------------- #
#
# Build-time purity for codegen.py is covered authoritatively by
# tests/unit/test_build_time_purity.py.


def _env(**over: object) -> EnvironmentModel:
    base: dict[str, object] = {
        "python_version": "3.12.13",
        "dependencies": [],
        "setup_instructions": "pyve init",
    }
    base.update(over)
    return EnvironmentModel.model_validate(base)


def test_ensure_marimo_pinned_passes_through_none() -> None:
    assert codegen.ensure_marimo_pinned(None) is None


def test_ensure_marimo_pinned_appends_marimo_when_absent() -> None:
    env = _env(dependencies=["numpy", "pandas"])
    out = codegen.ensure_marimo_pinned(env)
    assert out is not None
    deps = out["dependencies"]
    installed = _pkg_version("marimo")
    assert deps == ["numpy", "pandas", f"marimo>={installed}"]


def test_ensure_marimo_pinned_preserves_existing_unpinned_marimo() -> None:
    env = _env(dependencies=["marimo", "numpy"])
    out = codegen.ensure_marimo_pinned(env)
    assert out is not None
    assert out["dependencies"] == ["marimo", "numpy"]


def test_ensure_marimo_pinned_preserves_existing_pinned_marimo() -> None:
    env = _env(dependencies=["marimo==0.23.5", "numpy"])
    out = codegen.ensure_marimo_pinned(env)
    assert out is not None
    assert out["dependencies"] == ["marimo==0.23.5", "numpy"]


def test_ensure_marimo_pinned_preserves_marimo_with_extras() -> None:
    env = _env(dependencies=["marimo[lsp]>=0.23", "numpy"])
    out = codegen.ensure_marimo_pinned(env)
    assert out is not None
    assert out["dependencies"] == ["marimo[lsp]>=0.23", "numpy"]


def test_ensure_marimo_pinned_does_not_misidentify_other_packages() -> None:
    # Packages whose names start with "marimo" but are NOT marimo itself.
    env = _env(dependencies=["marimo-extension", "marimo_helper"])
    out = codegen.ensure_marimo_pinned(env)
    assert out is not None
    installed = _pkg_version("marimo")
    assert out["dependencies"] == ["marimo-extension", "marimo_helper", f"marimo>={installed}"]


def test_ensure_marimo_pinned_preserves_python_version_and_setup() -> None:
    env = _env(python_version="3.12.13", setup_instructions="pyve init && pip install -r ...")
    out = codegen.ensure_marimo_pinned(env)
    assert out is not None
    assert out["python_version"] == "3.12.13"
    assert out["setup_instructions"] == "pyve init && pip install -r ..."
