# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Option-C schema TDD smoke (Story I.b).

Small focused tests for the new input/output models. The authoritative
schema-acceptance/rejection sweep lives in Story I.e; this file just
covers the red-green-refactor cycle for I.b itself.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from nbfoundry import schema


def _definition(**over: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "title": "MPS smoke",
        "description": "Confirm torch sees Apple Metal.",
        "sections": [
            {
                "title": "Detect device",
                "description": "Pick MPS if available, else CPU.",
                "code": "import torch\ndevice = torch.device('cpu')\n",
            }
        ],
    }
    base.update(over)
    return base


# --------------------------------------------------------------------------- #
# ExerciseDefinition
# --------------------------------------------------------------------------- #


def test_exercise_definition_accepts_minimal() -> None:
    m = schema.ExerciseDefinition.model_validate(_definition())
    assert m.title == "MPS smoke"
    assert m.hints == []
    assert m.environment is None


def test_exercise_definition_requires_at_least_one_section() -> None:
    with pytest.raises(ValidationError):
        schema.ExerciseDefinition.model_validate(_definition(sections=[]))


def test_exercise_definition_rejects_legacy_expected_outputs_field() -> None:
    with pytest.raises(ValidationError):
        schema.ExerciseDefinition.model_validate(_definition(expected_outputs=[]))


def test_exercise_definition_rejects_legacy_submission_field() -> None:
    with pytest.raises(ValidationError):
        schema.ExerciseDefinition.model_validate(_definition(submission={"fields": []}))


def test_exercise_definition_accepts_hints_and_environment() -> None:
    m = schema.ExerciseDefinition.model_validate(
        _definition(
            hints=["Try `torch.backends.mps.is_available()`."],
            environment={
                "python_version": "3.12.13",
                "dependencies": ["marimo", "torch"],
                "setup_instructions": "pyve init && pip install -r requirements-torch.txt",
            },
        )
    )
    assert m.hints == ["Try `torch.backends.mps.is_available()`."]
    assert m.environment is not None and m.environment.dependencies == ["marimo", "torch"]


# --------------------------------------------------------------------------- #
# SectionModel
# --------------------------------------------------------------------------- #


def test_section_rejects_neither_code_nor_code_file() -> None:
    with pytest.raises(ValidationError):
        schema.ExerciseDefinition.model_validate(
            _definition(sections=[{"title": "s", "description": "d"}])
        )


def test_section_rejects_both_code_and_code_file() -> None:
    with pytest.raises(ValidationError):
        schema.ExerciseDefinition.model_validate(
            _definition(
                sections=[
                    {
                        "title": "s",
                        "description": "d",
                        "code": "x = 1",
                        "code_file": "a.py",
                    }
                ]
            )
        )


def test_section_rejects_legacy_editable_field() -> None:
    with pytest.raises(ValidationError):
        schema.ExerciseDefinition.model_validate(
            _definition(
                sections=[
                    {
                        "title": "s",
                        "description": "d",
                        "code": "x = 1",
                        "editable": True,
                    }
                ]
            )
        )


def test_section_hide_code_defaults_to_false() -> None:
    m = schema.ExerciseDefinition.model_validate(_definition())
    assert m.sections[0].hide_code is False


def test_section_accepts_hide_code_true() -> None:
    m = schema.ExerciseDefinition.model_validate(
        _definition(
            sections=[
                {
                    "title": "s",
                    "description": "d",
                    "code": "x = 1",
                    "hide_code": True,
                }
            ]
        )
    )
    assert m.sections[0].hide_code is True


def test_section_rejects_non_bool_hide_code() -> None:
    with pytest.raises(ValidationError):
        schema.ExerciseDefinition.model_validate(
            _definition(
                sections=[
                    {
                        "title": "s",
                        "description": "d",
                        "code": "x = 1",
                        "hide_code": {"not": "a bool"},
                    }
                ]
            )
        )


# --------------------------------------------------------------------------- #
# Retired names are gone
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "name",
    [
        "RawSectionModel",
        "RawExerciseModel",
        "RawExpectedOutputModel",
        "ExpectedRule",
        "SubmissionModel",
        "SubmissionFieldModel",
        "CompiledSection",
        "CompiledExpectedImage",
        "CompiledExpectedTextOrTable",
        "CompiledExpectedOutput",
        "CompiledSubmissionField",
        "CompiledSubmission",
    ],
)
def test_retired_schema_names_are_removed(name: str) -> None:
    assert not hasattr(schema, name), f"{name!r} should have been deleted in Story I.b"


# --------------------------------------------------------------------------- #
# CompiledExercise TypedDict shape
# --------------------------------------------------------------------------- #


def test_compiled_exercise_has_option_c_keys_only() -> None:
    expected = {
        "type",
        "source",
        "ref",
        "title",
        "description",
        "hints",
        "environment",
        "notebook_source",
    }
    assert set(schema.CompiledExercise.__annotations__.keys()) == expected
