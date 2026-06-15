# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Path-escape unit sweep (Story G.b) — SC-3: resolve_under safety."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from nbfoundry.errors import ExerciseError
from nbfoundry.paths import resolve_under


def test_resolve_under_returns_path_within_base(tmp_path: Path) -> None:
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "f.py").write_text("x", encoding="utf-8")
    resolved = resolve_under(tmp_path, "sub/f.py")
    assert resolved == (tmp_path / "sub" / "f.py").resolve()


def test_absolute_path_rejected(tmp_path: Path) -> None:
    with pytest.raises(ExerciseError, match="absolute paths not allowed"):
        resolve_under(tmp_path, "/etc/passwd")


def test_parent_escape_rejected(tmp_path: Path) -> None:
    # Target sits in tmp_path (one level above base) so `../` resolves to a real
    # file and the failure is the escape check, not a "does not exist" error.
    (tmp_path / "outside_target.py").write_text("x", encoding="utf-8")
    base = tmp_path / "base"
    base.mkdir()
    with pytest.raises(ExerciseError, match="escapes base directory"):
        resolve_under(base, "../outside_target.py")


def test_nonexistent_path_rejected(tmp_path: Path) -> None:
    with pytest.raises(ExerciseError, match="does not exist"):
        resolve_under(tmp_path, "nope.py")


def test_mixed_separator_resolves_within_base(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "b.py").write_text("x", encoding="utf-8")
    resolved = resolve_under(tmp_path, "a/b.py")
    assert resolved.name == "b.py"


@pytest.mark.skipif(sys.platform == "win32", reason="symlink semantics differ on Windows")
def test_symlink_escaping_base_rejected(tmp_path: Path) -> None:
    secret = tmp_path / "secret.py"
    secret.write_text("x", encoding="utf-8")
    base = tmp_path / "base"
    base.mkdir()
    (base / "link.py").symlink_to(secret)
    with pytest.raises(ExerciseError, match="escapes base directory"):
        resolve_under(base, "link.py")
