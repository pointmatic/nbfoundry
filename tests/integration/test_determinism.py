# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Integration: `compile_exercise` produces byte-stable output (Story I.e).

Two calls against the same definition must produce equal dicts. Two
fresh copies of the corpus must yield identical `notebook_source`
strings (the `ref` field is the only path-dependent value).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from nbfoundry.compiler import compile_exercise


def test_library_compile_is_deterministic(tmp_base_dir: Path, sample_yaml: Path) -> None:
    a = compile_exercise(sample_yaml, tmp_base_dir)
    b = compile_exercise(sample_yaml, tmp_base_dir)
    assert a == b


def test_compile_byte_stable_across_fresh_base_copies(
    tmp_path: Path, sample_yaml: Path, exercises_dir: Path
) -> None:
    base_a = tmp_path / "a" / "exercises"
    base_b = tmp_path / "b" / "exercises"
    shutil.copytree(exercises_dir, base_a)
    shutil.copytree(exercises_dir, base_b)

    out_a = compile_exercise(sample_yaml, base_a)
    out_b = compile_exercise(sample_yaml, base_b)
    # `notebook_source` is path-independent and must match byte-for-byte.
    assert out_a["notebook_source"] == out_b["notebook_source"]
    # JSON serialization with sort_keys=False must also be byte-stable.
    rendered_a = json.dumps(out_a, sort_keys=False, ensure_ascii=False, indent=2)
    rendered_b = json.dumps(out_b, sort_keys=False, ensure_ascii=False, indent=2)
    assert rendered_a == rendered_b
