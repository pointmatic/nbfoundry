# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import ast
import sys
import types
from pathlib import Path

import pytest

from nbfoundry._modelfoundry import ModelfoundryAdapter, get_adapter

_CORE_MODULES = ("compiler.py", "validator.py", "schema.py", "cli.py")


def test_get_adapter_raises_runtime_error_when_modelfoundry_missing() -> None:
    with pytest.raises(RuntimeError, match="modelfoundry is required"):
        get_adapter()


def test_get_adapter_returns_module_when_importable(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = types.ModuleType("modelfoundry")
    fake.prepare_data = lambda *a, **k: None  # type: ignore[attr-defined]
    fake.train = lambda *a, **k: None  # type: ignore[attr-defined]
    fake.optimize = lambda *a, **k: None  # type: ignore[attr-defined]
    fake.evaluate = lambda *a, **k: None  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "modelfoundry", fake)
    assert get_adapter() is fake


def test_adapter_protocol_is_runtime_checkable() -> None:
    class Good:
        def prepare_data(self, *a: object, **k: object) -> None: ...
        def train(self, *a: object, **k: object) -> None: ...
        def optimize(self, *a: object, **k: object) -> None: ...
        def evaluate(self, *a: object, **k: object) -> None: ...

    class Bad:
        def train(self, *a: object, **k: object) -> None: ...

    assert isinstance(Good(), ModelfoundryAdapter)
    assert not isinstance(Bad(), ModelfoundryAdapter)


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
