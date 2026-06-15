# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Schema unit sweep (Story G.b) — Pydantic accept/reject + BR-4 rule/type matrix."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from nbfoundry.schema import (
    ExpectedRule,
    RawExerciseModel,
    RawExpectedOutputModel,
    RawSectionModel,
    SubmissionFieldModel,
)


def _exercise(**over: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "title": "t",
        "description": "d",
        "sections": [{"title": "s", "description": "sd", "code": "x = 1"}],
    }
    base.update(over)
    return base


# --------------------------------------------------------------------------- #
# Accept
# --------------------------------------------------------------------------- #


def test_minimal_exercise_accepts() -> None:
    m = RawExerciseModel.model_validate(_exercise())
    assert m.title == "t"
    assert m.sections[0].editable is False
    assert m.expected_outputs == [] and m.hints == []
    assert m.submission is None and m.environment is None


def test_full_exercise_accepts() -> None:
    m = RawExerciseModel.model_validate(
        _exercise(
            expected_outputs=[{"description": "o", "type": "text", "content": "c"}],
            hints=["h1", "h2"],
            submission={
                "pass_threshold": 0.5,
                "fields": [
                    {
                        "name": "f",
                        "type": "number",
                        "label": "L",
                        "expected": {"type": "equals", "value": 1},
                    }
                ],
            },
            environment={
                "python_version": "3.12.13",
                "dependencies": ["numpy"],
                "setup_instructions": "pip install -r requirements-base.txt",
            },
        )
    )
    assert m.submission is not None and m.environment is not None


def test_section_accepts_code_file_alternative() -> None:
    s = RawSectionModel.model_validate({"title": "s", "description": "d", "code_file": "x.py"})
    assert s.code is None and s.code_file is not None


@pytest.mark.parametrize("threshold", [0.0, 0.5, 1.0])
def test_pass_threshold_bounds_accept(threshold: float) -> None:
    sub = {
        "pass_threshold": threshold,
        "fields": [
            {
                "name": "f",
                "type": "text",
                "label": "L",
                "expected": {"type": "equals", "value": "a"},
            }
        ],
    }
    RawExerciseModel.model_validate(_exercise(submission=sub))


def test_weight_defaults_to_one_and_accepts_positive() -> None:
    assert ExpectedRule.model_validate({"type": "equals", "value": 1}).weight == 1
    assert ExpectedRule.model_validate({"type": "equals", "value": 1, "weight": 5}).weight == 5


# --------------------------------------------------------------------------- #
# Reject — exercise / section
# --------------------------------------------------------------------------- #


def test_missing_title_rejects() -> None:
    bad = _exercise()
    del bad["title"]
    with pytest.raises(ValidationError):
        RawExerciseModel.model_validate(bad)


def test_unknown_key_rejects() -> None:
    with pytest.raises(ValidationError):
        RawExerciseModel.model_validate(_exercise(difficulty="hard"))


def test_empty_sections_rejects() -> None:
    with pytest.raises(ValidationError):
        RawExerciseModel.model_validate(_exercise(sections=[]))


def test_section_with_both_code_and_code_file_rejects() -> None:
    with pytest.raises(ValidationError, match="exactly one of"):
        RawSectionModel.model_validate(
            {"title": "s", "description": "d", "code": "x", "code_file": "x.py"}
        )


def test_section_with_neither_code_nor_code_file_rejects() -> None:
    with pytest.raises(ValidationError, match="exactly one of"):
        RawSectionModel.model_validate({"title": "s", "description": "d"})


# --------------------------------------------------------------------------- #
# Reject — expected outputs
# --------------------------------------------------------------------------- #


def test_image_output_requires_path_and_alt() -> None:
    with pytest.raises(ValidationError, match="image expected_outputs require"):
        RawExpectedOutputModel.model_validate(
            {"description": "o", "type": "image", "path": "a.png"}
        )


def test_image_output_must_not_carry_content() -> None:
    with pytest.raises(ValidationError, match="must not carry"):
        RawExpectedOutputModel.model_validate(
            {"description": "o", "type": "image", "path": "a.png", "alt": "x", "content": "c"}
        )


@pytest.mark.parametrize("kind", ["text", "table"])
def test_text_table_output_requires_content(kind: str) -> None:
    with pytest.raises(ValidationError, match="require `content`"):
        RawExpectedOutputModel.model_validate({"description": "o", "type": kind})


def test_text_output_must_not_carry_path() -> None:
    with pytest.raises(ValidationError, match="must not carry"):
        RawExpectedOutputModel.model_validate(
            {"description": "o", "type": "text", "content": "c", "path": "a.png"}
        )


# --------------------------------------------------------------------------- #
# Reject — expected rule shape
# --------------------------------------------------------------------------- #


def test_range_requires_min_or_max() -> None:
    with pytest.raises(ValidationError, match="at least one of `min` or `max`"):
        ExpectedRule.model_validate({"type": "range"})


def test_range_min_greater_than_max_rejects() -> None:
    with pytest.raises(ValidationError, match="`min` <= `max`"):
        ExpectedRule.model_validate({"type": "range", "min": 2, "max": 1})


def test_range_must_not_carry_value() -> None:
    with pytest.raises(ValidationError, match="must not carry"):
        ExpectedRule.model_validate({"type": "range", "min": 0, "value": 1})


def test_equals_requires_value() -> None:
    with pytest.raises(ValidationError, match="requires `value`"):
        ExpectedRule.model_validate({"type": "equals"})


def test_equals_must_not_carry_minmax() -> None:
    with pytest.raises(ValidationError, match="must not carry"):
        ExpectedRule.model_validate({"type": "equals", "value": 1, "min": 0})


def test_contains_all_requires_values() -> None:
    with pytest.raises(ValidationError, match="non-empty `values`"):
        ExpectedRule.model_validate({"type": "contains_all", "values": []})


def test_contains_all_must_not_carry_value() -> None:
    with pytest.raises(ValidationError, match="must not carry"):
        ExpectedRule.model_validate({"type": "contains_all", "values": ["a"], "value": 1})


@pytest.mark.parametrize("weight", [0, -1])
def test_weight_must_be_positive(weight: int) -> None:
    with pytest.raises(ValidationError):
        ExpectedRule.model_validate({"type": "equals", "value": 1, "weight": weight})


# --------------------------------------------------------------------------- #
# Reject — BR-4 rule/type compatibility matrix
# --------------------------------------------------------------------------- #


def _field(ftype: str, rule: dict[str, Any]) -> dict[str, Any]:
    return {"name": "f", "type": ftype, "label": "L", "expected": rule}


def test_range_rule_requires_number_field() -> None:
    with pytest.raises(ValidationError, match="`range` rule requires field type `number`"):
        SubmissionFieldModel.model_validate(_field("text", {"type": "range", "min": 0, "max": 1}))


def test_contains_all_rule_requires_text_field() -> None:
    with pytest.raises(ValidationError, match="`contains_all` rule requires field type `text`"):
        SubmissionFieldModel.model_validate(
            _field("number", {"type": "contains_all", "values": ["a"]})
        )


def test_equals_number_field_requires_numeric_value() -> None:
    with pytest.raises(ValidationError, match="requires a numeric `value`"):
        SubmissionFieldModel.model_validate(_field("number", {"type": "equals", "value": "x"}))


def test_equals_text_field_requires_string_value() -> None:
    with pytest.raises(ValidationError, match="requires a string `value`"):
        SubmissionFieldModel.model_validate(_field("text", {"type": "equals", "value": 1}))


@pytest.mark.parametrize(
    "ftype,rule",
    [
        ("number", {"type": "range", "min": 0, "max": 1}),
        ("text", {"type": "contains_all", "values": ["a"]}),
        ("number", {"type": "equals", "value": 1}),
        ("text", {"type": "equals", "value": "a"}),
    ],
)
def test_compatible_rule_field_pairs_accept(ftype: str, rule: dict[str, Any]) -> None:
    SubmissionFieldModel.model_validate(_field(ftype, rule))


def test_pass_threshold_out_of_range_rejects() -> None:
    sub = {"pass_threshold": 1.5, "fields": [_field("number", {"type": "equals", "value": 1})]}
    with pytest.raises(ValidationError):
        RawExerciseModel.model_validate(_exercise(submission=sub))


def test_submission_requires_at_least_one_field() -> None:
    with pytest.raises(ValidationError):
        RawExerciseModel.model_validate(_exercise(submission={"fields": []}))


def test_duplicate_field_names_reject() -> None:
    sub = {
        "fields": [
            _field("number", {"type": "equals", "value": 1}),
            _field("number", {"type": "equals", "value": 2}),
        ]
    }
    with pytest.raises(ValidationError, match="duplicate submission field name"):
        RawExerciseModel.model_validate(_exercise(submission=sub))
