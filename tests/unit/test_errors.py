# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Errors unit sweep — `ExerciseError` shape and Pydantic → ExerciseError mapping."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from nbfoundry.errors import ErrorDetail, ExerciseError, from_pydantic
from nbfoundry.schema import ExerciseDefinition


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
        # section is missing the code XOR code_file constraint
        "sections": [{"title": "S", "description": "b"}],
    }
    try:
        ExerciseDefinition.model_validate(bad)
    except ValidationError as ve:
        errors = from_pydantic(Path("ex.yaml"), ve)
    else:  # pragma: no cover - must raise
        raise AssertionError("expected ValidationError")

    assert errors
    assert all(isinstance(e, ExerciseError) for e in errors)
    assert all(e.file_path == Path("ex.yaml") for e in errors)
    assert any(e.detail is not None and e.detail.section_index == 0 for e in errors)


def test_from_pydantic_augments_scalar_input() -> None:
    bad = {
        "title": "T",
        "description": "d",
        # `editable` is a retired Option-B field; Pydantic rejects under
        # extra="forbid" and the rejection should surface the offending
        # input value in the error message.
        "sections": [
            {
                "title": "S",
                "description": "b",
                "code": "x = 1",
                "editable": True,
            }
        ],
    }
    try:
        ExerciseDefinition.model_validate(bad)
    except ValidationError as ve:
        errors = from_pydantic(Path("ex.yaml"), ve)
    else:  # pragma: no cover
        raise AssertionError("expected ValidationError")

    assert any("True" in e.message for e in errors)
