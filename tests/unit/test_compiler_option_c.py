# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Option-C compile/validate TDD smoke (Story I.d).

Small focused tests for the rewired `compile_exercise` + `validate_exercise`.
The authoritative integration sweep lives in Story I.e (CLI end-to-end,
marimo-loads-generated-module smoke); this file covers the red-green
cycle for I.d itself plus the build-time purity AC-10 carry-forward.
"""

from __future__ import annotations

import ast
import textwrap
from importlib.metadata import version as _pkg_version
from pathlib import Path

import pytest

from nbfoundry.compiler import compile_exercise, validate_exercise
from nbfoundry.errors import ExerciseError

_MIN_DEFN_YAML = textwrap.dedent(
    """\
    title: MPS smoke
    description: "Confirm torch sees Apple Metal."
    sections:
      - title: Detect device
        description: "Pick MPS if available, else CPU."
        code: |
          import torch
          device = torch.device('cpu')
    """
)


def _write_yaml(base: Path, text: str = _MIN_DEFN_YAML, name: str = "ex.yaml") -> Path:
    p = base / name
    p.write_text(text, encoding="utf-8")
    return Path(name)


# --------------------------------------------------------------------------- #
# Happy path
# --------------------------------------------------------------------------- #


def test_compile_returns_option_c_dict_with_exactly_eight_keys(tmp_path: Path) -> None:
    rel = _write_yaml(tmp_path)
    out = compile_exercise(rel, tmp_path)
    assert set(out.keys()) == {
        "type",
        "source",
        "ref",
        "title",
        "description",
        "hints",
        "environment",
        "notebook_source",
    }


def test_compile_sets_type_source_ref(tmp_path: Path) -> None:
    rel = _write_yaml(tmp_path)
    out = compile_exercise(rel, tmp_path)
    assert out["type"] == "exercise"
    assert out["source"] == "nbfoundry"
    assert out["ref"] == "ex.yaml"


def test_compile_renders_description_as_html(tmp_path: Path) -> None:
    rel = _write_yaml(
        tmp_path,
        textwrap.dedent(
            """\
            title: T
            description: "**bold** matters"
            sections:
              - title: s
                description: "d"
                code: "x = 1\\n"
            """
        ),
    )
    out = compile_exercise(rel, tmp_path)
    assert "<strong>bold</strong>" in out["description"]


def test_compile_renders_hints_as_html(tmp_path: Path) -> None:
    rel = _write_yaml(
        tmp_path,
        textwrap.dedent(
            """\
            title: T
            description: "d"
            hints:
              - "first *hint*"
              - "second hint"
            sections:
              - title: s
                description: "d"
                code: "x = 1\\n"
            """
        ),
    )
    out = compile_exercise(rel, tmp_path)
    assert len(out["hints"]) == 2
    assert "<em>hint</em>" in out["hints"][0]


def test_compile_notebook_source_is_valid_python_module(tmp_path: Path) -> None:
    rel = _write_yaml(tmp_path)
    out = compile_exercise(rel, tmp_path)
    ast.parse(out["notebook_source"])
    assert out["notebook_source"].startswith("import marimo\n")


def test_compile_environment_none_when_omitted(tmp_path: Path) -> None:
    rel = _write_yaml(tmp_path)
    out = compile_exercise(rel, tmp_path)
    assert out["environment"] is None


def test_compile_environment_pins_marimo_when_author_supplies_env_without_it(
    tmp_path: Path,
) -> None:
    rel = _write_yaml(
        tmp_path,
        textwrap.dedent(
            """\
            title: T
            description: "d"
            environment:
              python_version: "3.12.13"
              dependencies: ["numpy"]
              setup_instructions: "pyve init"
            sections:
              - title: s
                description: "d"
                code: "x = 1\\n"
            """
        ),
    )
    out = compile_exercise(rel, tmp_path)
    env = out["environment"]
    assert env is not None
    expected_pin = f"marimo>={_pkg_version('marimo')}"
    assert expected_pin in env["dependencies"]


def test_compile_inlines_code_file(tmp_path: Path) -> None:
    (tmp_path / "section.py").write_text("y = 99\n", encoding="utf-8")
    rel = _write_yaml(
        tmp_path,
        textwrap.dedent(
            """\
            title: T
            description: "d"
            sections:
              - title: s
                description: "d"
                code_file: "section.py"
            """
        ),
    )
    out = compile_exercise(rel, tmp_path)
    assert "y = 99" in out["notebook_source"]


def test_compile_is_deterministic(tmp_path: Path) -> None:
    rel = _write_yaml(tmp_path)
    a = compile_exercise(rel, tmp_path)
    b = compile_exercise(rel, tmp_path)
    assert a == b


# --------------------------------------------------------------------------- #
# Error paths — first-error semantics
# --------------------------------------------------------------------------- #


def test_compile_raises_on_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ExerciseError):
        compile_exercise(Path("missing.yaml"), tmp_path)


def test_compile_raises_on_schema_failure(tmp_path: Path) -> None:
    rel = _write_yaml(
        tmp_path,
        textwrap.dedent(
            """\
            title: T
            description: "d"
            sections: []
            """
        ),
    )
    with pytest.raises(ExerciseError):
        compile_exercise(rel, tmp_path)


def test_compile_raises_on_legacy_field(tmp_path: Path) -> None:
    rel = _write_yaml(
        tmp_path,
        textwrap.dedent(
            """\
            title: T
            description: "d"
            expected_outputs: []
            sections:
              - title: s
                description: "d"
                code: "x = 1\\n"
            """
        ),
    )
    with pytest.raises(ExerciseError):
        compile_exercise(rel, tmp_path)


def test_compile_raises_on_code_file_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.py"
    outside.write_text("y = 1\n", encoding="utf-8")
    try:
        rel = _write_yaml(
            tmp_path,
            textwrap.dedent(
                """\
                title: T
                description: "d"
                sections:
                  - title: s
                    description: "d"
                    code_file: "../outside.py"
                """
            ),
        )
        with pytest.raises(ExerciseError):
            compile_exercise(rel, tmp_path)
    finally:
        outside.unlink(missing_ok=True)


def test_compile_raises_on_non_mapping_yaml(tmp_path: Path) -> None:
    rel = _write_yaml(tmp_path, "- just\n- a\n- list\n")
    with pytest.raises(ExerciseError):
        compile_exercise(rel, tmp_path)


# --------------------------------------------------------------------------- #
# validate_exercise
# --------------------------------------------------------------------------- #


def test_validate_returns_empty_list_on_valid_definition(tmp_path: Path) -> None:
    rel = _write_yaml(tmp_path)
    assert validate_exercise(rel, tmp_path) == []


def test_validate_returns_single_item_on_missing_file(tmp_path: Path) -> None:
    errs = validate_exercise(Path("missing.yaml"), tmp_path)
    assert len(errs) == 1


def test_validate_returns_strings_on_schema_failures(tmp_path: Path) -> None:
    rel = _write_yaml(
        tmp_path,
        textwrap.dedent(
            """\
            title: T
            description: "d"
            sections:
              - title: s
                description: "d"
                code: "x = 1"
                code_file: "x.py"
            """
        ),
    )
    errs = validate_exercise(rel, tmp_path)
    assert len(errs) >= 1
    assert all(isinstance(e, str) for e in errs)
    # The error string should mention the file (path + colon).
    assert any("ex.yaml" in e for e in errs)


# --------------------------------------------------------------------------- #
# Build-time purity (AC-10 carry-forward for compiler.py)
# --------------------------------------------------------------------------- #


_FORBIDDEN_BUILD_TIME_IMPORTS = frozenset(
    {
        "torch",
        "tensorflow",
        "keras",
        "transformers",
        "datasets",
        "peft",
        "sentencepiece",
        "tiktoken",
        "optuna",
        "modelfoundry",
        "datarefinery",
    }
)


def test_compiler_module_has_no_build_time_ml_imports() -> None:
    from nbfoundry import compiler

    src = Path(compiler.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    offenders: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in _FORBIDDEN_BUILD_TIME_IMPORTS:
                    offenders.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in _FORBIDDEN_BUILD_TIME_IMPORTS:
                offenders.append(node.module or "")
    assert offenders == [], f"compiler.py imports ML framework(s) at build time: {offenders}"
