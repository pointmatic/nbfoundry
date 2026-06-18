# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Authoritative no-ML-import AST scan over the Option-C compile path.

AC-10 / FR-7: `compile_exercise` must run inside LearningFoundry's build
process without pulling a multi-hundred-MB ML framework. Framework
imports (`import torch`, `import tensorflow`, ...) appear only as source
text inside emitted marimo cells; they are imported at notebook run time
on the learner's machine, never at build time.

This file is the **authoritative** scan: it walks each module on the
build-time compile path and asserts that none of them imports anything
from the forbidden set. The `_modelfoundry.py` boundary intentionally
declares `modelfoundry` as a Protocol/lazy-import target and is excluded
— but the test asserts `compiler.py`, `codegen.py`, etc. do NOT import
`_modelfoundry` either, carrying forward the original Phase B guarantee.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

import nbfoundry

_NBFOUNDRY_DIR = Path(nbfoundry.__file__).parent

# Packages whose presence as an `import` at build time would constitute
# a contract violation. Sourced from the project-essentials build-time
# purity rule (`Build-time purity is load-bearing under Option C`).
_FORBIDDEN: frozenset[str] = frozenset(
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

# Modules on the build-time compile path. Every one of these is executed
# (directly or transitively) when LearningFoundry imports
# `nbfoundry.compile_exercise`.
_BUILD_TIME_MODULES: tuple[str, ...] = (
    "__init__.py",
    "schema.py",
    "compiler.py",
    "codegen.py",
    "cli.py",
    "config.py",
    "errors.py",
    "logging_setup.py",
    "markdown.py",
    "notebooks.py",
    "paths.py",
    "standalone.py",
)


def _ml_imports(module_path: Path) -> list[str]:
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    bad: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in _FORBIDDEN:
                    bad.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in _FORBIDDEN:
                bad.append(node.module or "<relative>")
    return bad


@pytest.mark.parametrize("module_filename", _BUILD_TIME_MODULES)
def test_build_time_module_has_no_ml_imports(module_filename: str) -> None:
    module_path = _NBFOUNDRY_DIR / module_filename
    assert module_path.is_file(), (
        f"build-time module {module_filename} not found at {module_path}; "
        "update _BUILD_TIME_MODULES if the package layout changed"
    )
    offenders = _ml_imports(module_path)
    assert offenders == [], (
        f"{module_filename} imports {offenders} at build time; "
        "ML frameworks must appear only as source text inside emitted cells "
        "(see project-essentials.md § 'Build-time purity is load-bearing under Option C')"
    )


def test_modelfoundry_boundary_module_is_not_imported_by_compile_path() -> None:
    """The `_modelfoundry.py` boundary is excluded from the scan because it
    declares the lazy-import target on purpose. But none of the compile-path
    modules above should import the boundary either — the Phase B AC-10
    guarantee that the compiler core never reaches into modelfoundry.
    """
    offenders: dict[str, list[str]] = {}
    for filename in _BUILD_TIME_MODULES:
        module_path = _NBFOUNDRY_DIR / filename
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        bad: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.endswith("_modelfoundry") or alias.name.endswith(".modelfoundry"):
                        bad.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod.endswith("_modelfoundry") or mod == "modelfoundry":
                    bad.append(mod)
        if bad:
            offenders[filename] = bad
    assert offenders == {}, (
        f"build-time compile path imports the modelfoundry boundary: {offenders}"
    )
