# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Shared pytest fixtures for the nbfoundry test suite (Story G.a).

Exposes the fixture corpus under `tests/fixtures/` to the unit and integration
suites: read-only path fixtures, a writable copy of the exercise corpus to use
as a compile `base_dir`, a representative sample YAML path, and the golden
compiled dict.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
EXERCISES_DIR = FIXTURES_DIR / "exercises"
GOLDEN_DIR = FIXTURES_DIR / "golden"

# --- Phase I Option-C transition (Stories I.b → I.e) ---------------------
# Tests written against the retired Option-B static-display schema/compiler
# contract import names that no longer exist (Story I.b deleted the models,
# Story I.b stubbed compiler.py to NotImplementedError). They are scheduled
# for removal in Story I.e. Until then, collect_ignore keeps pytest from
# aborting at collection time on their top-level ImportErrors so the rest
# of the suite continues to run.
collect_ignore = [
    "unit/test_schema.py",
    "unit/test_errors.py",
]


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

    Includes the valid/invalid YAMLs, the `assets/` directory, and the `tree/`
    fixture, so tests can `compile_exercise(rel_path, tmp_base_dir)` against a
    base that mirrors what ships in the repo without mutating the source corpus.
    """
    dst = tmp_path / "exercises"
    shutil.copytree(EXERCISES_DIR, dst)
    return dst


@pytest.fixture
def sample_yaml() -> Path:
    """Relative path (under a `base_dir`) of a representative valid exercise.

    Paired with `golden_dict`: `compile_exercise(sample_yaml, base)` is expected
    to equal `golden_dict`.
    """
    return Path("valid_graded.yaml")


@pytest.fixture
def golden_dict() -> dict[str, Any]:
    """The byte-for-byte golden compiled dict for `valid_graded.yaml` (TR-2)."""
    return json.loads((GOLDEN_DIR / "valid_graded.json").read_text(encoding="utf-8"))
