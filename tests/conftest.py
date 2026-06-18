# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Shared pytest fixtures for the nbfoundry test suite (Option C, Story I.e).

Exposes the Option-C fixture corpus under `tests/fixtures/` to the unit
and integration suites: read-only path fixtures, a writable copy of the
exercise corpus to use as a compile `base_dir`, and the relative path of
the canonical minimal exercise.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
EXERCISES_DIR = FIXTURES_DIR / "exercises"


@pytest.fixture
def fixtures_dir() -> Path:
    """Absolute path to `tests/fixtures/`."""
    return FIXTURES_DIR


@pytest.fixture
def exercises_dir() -> Path:
    """Absolute path to the read-only exercise-YAML corpus."""
    return EXERCISES_DIR


@pytest.fixture
def tmp_base_dir(tmp_path: Path) -> Path:
    """A writable copy of the exercise corpus, usable as a compile `base_dir`.

    Includes `valid_minimal.yaml` and the `tree/` fixture so tests can
    `compile_exercise(rel_path, tmp_base_dir)` against a base that mirrors
    what ships in the repo without mutating the source corpus.
    """
    dst = tmp_path / "exercises"
    shutil.copytree(EXERCISES_DIR, dst)
    return dst


@pytest.fixture
def sample_yaml() -> Path:
    """Relative path (under a `base_dir`) of the canonical minimal exercise."""
    return Path("valid_minimal.yaml")
