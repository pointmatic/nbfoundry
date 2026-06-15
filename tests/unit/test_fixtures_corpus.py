# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Smoke test for the G.a fixture corpus + shared conftest fixtures.

Proves the corpus is *real* (valid fixtures compile, invalid ones reject, the
golden matches the compiler) and that the shared conftest fixtures
(`tmp_base_dir`, `sample_yaml`, `golden_dict`) are importable and usable. This
is the Story G.a verify; the exhaustive matrices live in G.b / G.c.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nbfoundry.compiler import compile_exercise, validate_exercise

VALID = ["valid_minimal.yaml", "valid_graded.yaml", "valid_with_assets.yaml"]


def test_corpus_files_present(exercises_dir: Path, fixtures_dir: Path) -> None:
    for name in VALID:
        assert (exercises_dir / name).is_file()
    assert (exercises_dir / "assets" / "plot.png").is_file()
    assert (exercises_dir / "tree" / "exercise.yaml").is_file()
    assert sorted((exercises_dir / "tree" / "notebooks").glob("*.py"))
    assert (fixtures_dir / "golden" / "valid_graded.json").is_file()
    # At least the two tech-spec-named invalid fixtures exist.
    assert (exercises_dir / "invalid_pass_threshold_out_of_range.yaml").is_file()
    assert (exercises_dir / "invalid_duplicate_field_name.yaml").is_file()


def test_valid_fixtures_compile_clean(tmp_base_dir: Path) -> None:
    for name in VALID:
        assert validate_exercise(Path(name), tmp_base_dir) == [], name


def test_tree_fixture_compiles(tmp_base_dir: Path) -> None:
    tree_base = tmp_base_dir / "tree"
    compiled = compile_exercise(Path("exercise.yaml"), tree_base)
    # Both tree-internal notebooks were inlined into their sections.
    assert len(compiled["sections"]) == 2
    assert "data = [1, 2, 3]" in compiled["sections"][0]["code"]


def test_every_invalid_fixture_is_rejected(tmp_base_dir: Path) -> None:
    invalid = sorted(tmp_base_dir.glob("invalid_*.yaml"))
    assert len(invalid) >= 10, "expected a broad invalid-fixture corpus"
    for p in invalid:
        errors = validate_exercise(Path(p.name), tmp_base_dir)
        assert errors, f"{p.name} should have been rejected but validated clean"


def test_sample_compiles_to_golden(
    tmp_base_dir: Path, sample_yaml: Path, golden_dict: dict[str, Any]
) -> None:
    compiled = compile_exercise(sample_yaml, tmp_base_dir)
    assert compiled == golden_dict
