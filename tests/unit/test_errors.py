# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Errors unit sweep (Story G.b) — ExerciseError shape + Pydantic mapping."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from nbfoundry.errors import ErrorDetail, ExerciseError, from_pydantic
from nbfoundry.schema import RawExerciseModel


def test_exercise_error_str_without_detail() -> None:
    e = ExerciseError(Path("/a/b.yaml"), "boom")
    assert str(e) == "/a/b.yaml: boom"


def test_exercise_error_str_with_detail() -> None:
    e = ExerciseError(Path("/a/b.yaml"), "boom", ErrorDetail(section_index=2, field_name="x"))
    assert str(e) == "/a/b.yaml: boom [section=2, field=x]"


def test_exercise_error_is_raisable() -> None:
    with pytest.raises(ExerciseError):
        raise ExerciseError(Path("p"), "m")


def test_error_detail_str_empty() -> None:
    assert str(ErrorDetail()) == "ErrorDetail()"


def test_error_detail_str_orders_pointer_section_field() -> None:
    d = ErrorDetail(section_index=1, field_name="f", yaml_pointer="sections[1].code")
    assert str(d) == "sections[1].code, section=1, field=f"


def test_from_pydantic_maps_section_index_and_pointer() -> None:
    bad = {
        "title": "T",
        "description": "d",
        "sections": [{"title": "S", "description": "b"}],  # missing code xor
    }
    try:
        RawExerciseModel.model_validate(bad)
    except ValidationError as ve:
        errors = from_pydantic(Path("ex.yaml"), ve)
    else:  # pragma: no cover - must raise
        raise AssertionError("expected ValidationError")

    assert errors
    assert all(isinstance(e, ExerciseError) for e in errors)
    assert all(e.file_path == Path("ex.yaml") for e in errors)
    # the failing section is index 0
    assert any(e.detail is not None and e.detail.section_index == 0 for e in errors)


def test_from_pydantic_augments_scalar_input() -> None:
    bad = {
        "title": "T",
        "description": "d",
        "sections": [{"title": "S", "description": "b", "code": "x"}],
        "submission": {
            "pass_threshold": 1.5,
            "fields": [
                {
                    "name": "f",
                    "type": "number",
                    "label": "L",
                    "expected": {"type": "equals", "value": 1},
                }
            ],
        },
    }
    try:
        RawExerciseModel.model_validate(bad)
    except ValidationError as ve:
        errors = from_pydantic(Path("ex.yaml"), ve)
    else:  # pragma: no cover
        raise AssertionError("expected ValidationError")

    assert any("1.5" in e.message for e in errors)
