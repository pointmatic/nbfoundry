# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Assets unit sweep (Story G.b) — BR-5 enumeration + existence + size thresholds."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from nbfoundry import assets
from nbfoundry.errors import ExerciseError

_MB = 1024 * 1024


# --------------------------------------------------------------------------- #
# enumerate
# --------------------------------------------------------------------------- #


def test_enumerate_collects_only_image_paths_sorted_unique() -> None:
    out = assets.enumerate(
        [
            {"type": "image", "path": "b.png"},
            {"type": "image", "path": "a.png"},
            {"type": "image", "path": "a.png"},  # duplicate
            {"type": "text", "content": "c"},  # non-image ignored
            {"type": "image"},  # no path ignored
        ]
    )
    assert out == ["a.png", "b.png"]


def test_enumerate_empty() -> None:
    assert assets.enumerate([]) == []


# --------------------------------------------------------------------------- #
# check_existence
# --------------------------------------------------------------------------- #


def test_check_existence_passes_for_present_file(tmp_path: Path) -> None:
    (tmp_path / "a.png").write_bytes(b"x")
    assets.check_existence(tmp_path, ["a.png"])  # no raise


def test_check_existence_rejects_missing(tmp_path: Path) -> None:
    with pytest.raises(ExerciseError, match="does not exist"):
        assets.check_existence(tmp_path, ["missing.png"])


def test_check_existence_rejects_url(tmp_path: Path) -> None:
    with pytest.raises(ExerciseError, match="not URLs"):
        assets.check_existence(tmp_path, ["https://example.com/a.png"])


# --------------------------------------------------------------------------- #
# check_size
# --------------------------------------------------------------------------- #


def _make(tmp_path: Path, name: str, mb: float) -> str:
    (tmp_path / name).write_bytes(b"\0" * int(mb * _MB))
    return name


def test_check_size_under_threshold_silent(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    name = _make(tmp_path, "small.png", 1)
    with caplog.at_level(logging.WARNING, logger="nbfoundry.assets"):
        assets.check_size(tmp_path, [name], warn_mb=5, max_mb=10, allow_large=False)
    assert not caplog.records


def test_check_size_warns_between_warn_and_max(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    name = _make(tmp_path, "mid.png", 6)
    with caplog.at_level(logging.WARNING, logger="nbfoundry.assets"):
        assets.check_size(tmp_path, [name], warn_mb=5, max_mb=10, allow_large=False)
    assert any("mid.png" in r.message for r in caplog.records)


def test_check_size_errors_at_or_above_max(tmp_path: Path) -> None:
    name = _make(tmp_path, "big.png", 11)
    with pytest.raises(ExerciseError, match="exceeds"):
        assets.check_size(tmp_path, [name], warn_mb=5, max_mb=10, allow_large=False)


def test_check_size_allow_large_bypasses_max(tmp_path: Path) -> None:
    name = _make(tmp_path, "big.png", 11)
    assets.check_size(tmp_path, [name], warn_mb=5, max_mb=10, allow_large=True)  # no raise


def test_check_size_rejects_url(tmp_path: Path) -> None:
    with pytest.raises(ExerciseError, match="not URLs"):
        assets.check_size(tmp_path, ["http://x/a.png"], warn_mb=5, max_mb=10, allow_large=False)
