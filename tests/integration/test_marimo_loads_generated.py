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

import marimo

from nbfoundry.compiler import compile_exercise


def test_generated_notebook_imports_and_exposes_marimo_app_instance(
    tmp_base_dir: Path, sample_yaml: Path, tmp_path: Path
) -> None:
    compiled = compile_exercise(sample_yaml, tmp_base_dir)

    out_path = tmp_path / "generated.py"
    out_path.write_text(compiled["notebook_source"], encoding="utf-8")

    spec = importlib.util.spec_from_file_location("nbfoundry_generated_smoke", out_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)

    assert hasattr(module, "app"), "generated module must expose a top-level `app`"
    assert isinstance(module.app, marimo.App)
