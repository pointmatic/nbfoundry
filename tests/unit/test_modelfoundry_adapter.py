# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from nbfoundry._modelfoundry import get_adapter

_CORE_MODULES = ("compiler.py", "validator.py", "schema.py", "cli.py")


def test_get_adapter_raises_runtime_error_when_modelfoundry_missing() -> None:
    with pytest.raises(RuntimeError, match="modelfoundry is required"):
        get_adapter()


def test_compiler_core_does_not_import_modelfoundry_adapter() -> None:
    src = Path(__file__).resolve().parents[2] / "src" / "nbfoundry"
    offenders: list[str] = []
    for filename in _CORE_MODULES:
        path = src / filename
        if not path.is_file():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.endswith("_modelfoundry"):
                        offenders.append(f"{filename}: import {alias.name}")
            elif (
                isinstance(node, ast.ImportFrom)
                and node.module is not None
                and node.module.endswith("_modelfoundry")
            ):
                offenders.append(f"{filename}: from {node.module} import ...")
    assert not offenders, f"compiler core must not import _modelfoundry: {offenders}"
