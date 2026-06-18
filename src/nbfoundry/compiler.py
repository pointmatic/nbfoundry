# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Compiler module — Option C transition stub (Story I.b).

The Option-B static-display pipeline is gone with the Option-C schema
redline (Story I.b). The Option-C pipeline lands in Story I.d (`compile_exercise`
returns `{type, source, ref, title, description, hints, environment,
notebook_source}`, with `notebook_source` produced by `codegen.generate()`).

In the meantime, the package must remain importable so unrelated test
collection (paths, markdown, config, …) still runs and so downstream
modules that re-export `compile_exercise` / `validate_exercise` don't
explode at import time. Both entry points are kept as defined symbols and
raise `NotImplementedError` on call; the Story I.d rewrite restores them.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

_I_D_NOT_LANDED = (
    "compile_exercise / validate_exercise are temporarily unavailable "
    "between Story I.b (schema redline) and Story I.d (compiler rewire). "
    "See docs/specs/phase-i-learningfoundry-integration-refactoring-plan.md."
)


def compile_exercise(
    yaml_path: Path,
    base_dir: Path,
    *,
    allow_large_assets: bool = False,
) -> dict[str, Any]:
    raise NotImplementedError(_I_D_NOT_LANDED)


def validate_exercise(yaml_path: Path, base_dir: Path) -> list[str]:
    raise NotImplementedError(_I_D_NOT_LANDED)
