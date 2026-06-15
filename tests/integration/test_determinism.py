# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Integration: deterministic, byte-stable compile output (Story G.c, OR-5)."""

from __future__ import annotations

import json
from pathlib import Path

from nbfoundry.compiler import compile_exercise


def _serialize(obj: object) -> str:
    return json.dumps(obj, sort_keys=False, ensure_ascii=False, separators=(",", ": "), indent=2)


def test_library_compile_is_deterministic(tmp_base_dir: Path, sample_yaml: Path) -> None:
    first = compile_exercise(sample_yaml, tmp_base_dir)
    second = compile_exercise(sample_yaml, tmp_base_dir)
    assert first == second
    assert _serialize(first) == _serialize(second)


def test_compile_byte_stable_across_fresh_base_copies(
    tmp_base_dir: Path, sample_yaml: Path, tmp_path: Path
) -> None:
    import shutil

    other = tmp_path / "other_base"
    shutil.copytree(tmp_base_dir, other)
    a = _serialize(compile_exercise(sample_yaml, tmp_base_dir))
    b = _serialize(compile_exercise(sample_yaml, other))
    assert a == b
