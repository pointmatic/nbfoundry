# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Integration: marimo loads the generated notebook (Story I.e).

Compiles `valid_minimal.yaml` and loads the resulting `notebook_source`
via `importlib.util`. Confirms the module imports cleanly and exposes a
`marimo.App` instance. Importing (as opposed to `marimo run`) sets
`__name__` to the spec name, so the `if __name__ == "__main__":
app.run()` guard at the bottom of the generated module does NOT fire,
making this a fast unit-style smoke. The full hardware-driven `marimo
run` / `marimo edit` round-trip remains deferred to Story I.a's
developer-hardware verify step.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import marimo

from nbfoundry import codegen
from nbfoundry.compiler import compile_exercise
from nbfoundry.schema import ExerciseDefinition


def _load_module(source: str, out_path: Path, name: str) -> ModuleType:
    out_path.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(name, out_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


def test_generated_notebook_imports_and_exposes_marimo_app_instance(
    tmp_base_dir: Path, sample_yaml: Path, tmp_path: Path
) -> None:
    compiled = compile_exercise(sample_yaml, tmp_base_dir)
    module = _load_module(
        compiled["notebook_source"], tmp_path / "generated.py", "nbfoundry_generated_smoke"
    )

    assert hasattr(module, "app"), "generated module must expose a top-level `app`"
    assert isinstance(module.app, marimo.App)


def test_generated_notebook_with_hidden_code_loads(tmp_path: Path) -> None:
    # Story I.g: a `hide_code` cell must produce a module marimo can load —
    # i.e. `@app.cell(hide_code=True)` is a kwarg marimo's decorator accepts.
    defn = ExerciseDefinition.model_validate(
        {
            "title": "Hidden cell",
            "description": "The setup cell's code is hidden.",
            "sections": [
                {
                    "title": "Setup",
                    "description": "Hidden setup.",
                    "code": "x = 1\n",
                    "hide_code": True,
                }
            ],
        }
    )
    source = codegen.generate(defn, base_dir=tmp_path)
    assert "@app.cell(hide_code=True)" in source
    module = _load_module(source, tmp_path / "hidden.py", "nbfoundry_hidecode_smoke")

    assert isinstance(module.app, marimo.App)
