# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Literal, Self, TypedDict

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, model_validator

# ---------------------------------------------------------------------------
# Input models (parsed from YAML)
# ---------------------------------------------------------------------------


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RawSectionModel(_StrictModel):
    title: str
    description: str
    code: str | None = None
    code_file: Path | None = None
    editable: bool = False

    @model_validator(mode="after")
    def code_xor_code_file(self) -> Self:
        if (self.code is None) == (self.code_file is None):
            raise ValueError("exactly one of `code` or `code_file` is required")
        return self


class RawExpectedOutputModel(_StrictModel):
    description: str
    type: Literal["image", "text", "table"]
    path: Path | None = None
    alt: str | None = None
    content: str | None = None

    @model_validator(mode="after")
    def shape_by_type(self) -> Self:
        if self.type == "image":
            if not self.path or not self.alt:
                raise ValueError("image expected_outputs require both `path` and `alt`")
            if self.content is not None:
                raise ValueError("image expected_outputs must not carry `content`")
        else:
            if self.content is None:
                raise ValueError(f"{self.type} expected_outputs require `content`")
            if self.path is not None or self.alt is not None:
                raise ValueError(f"{self.type} expected_outputs must not carry `path`/`alt`")
        return self


class ExpectedRule(_StrictModel):
    type: Literal["range", "equals", "contains_all"]
    min: float | None = None
    max: float | None = None
    value: float | str | None = None
    values: list[str] | None = None
    weight: PositiveInt = 1

    @model_validator(mode="after")
    def required_keys_per_type(self) -> Self:
        if self.type == "range":
            if self.min is None and self.max is None:
                raise ValueError("`range` rule requires at least one of `min` or `max`")
            if self.min is not None and self.max is not None and self.min > self.max:
                raise ValueError("`range` rule requires `min` <= `max`")
            if self.value is not None or self.values is not None:
                raise ValueError("`range` rule must not carry `value` or `values`")
        elif self.type == "equals":
            if self.value is None:
                raise ValueError("`equals` rule requires `value`")
            if self.min is not None or self.max is not None or self.values is not None:
                raise ValueError("`equals` rule must not carry `min`/`max`/`values`")
        else:  # contains_all
            if not self.values:
                raise ValueError("`contains_all` rule requires non-empty `values`")
            if self.min is not None or self.max is not None or self.value is not None:
                raise ValueError("`contains_all` rule must not carry `min`/`max`/`value`")
        return self


class SubmissionFieldModel(_StrictModel):
    name: str
    type: Literal["number", "text"]
    label: str
    placeholder: str | None = None
    expected: ExpectedRule

    @model_validator(mode="after")
    def rule_type_compat(self) -> Self:
        rule = self.expected.type
        ftype = self.type
        name = self.name
        if rule == "range" and ftype != "number":
            raise ValueError(
                f"field {name!r}: `range` rule requires field type `number`, got `{ftype}`"
            )
        if rule == "contains_all" and ftype != "text":
            raise ValueError(
                f"field {name!r}: `contains_all` rule requires field type `text`, got `{ftype}`"
            )
        if rule == "equals":
            value = self.expected.value
            if ftype == "number" and not isinstance(value, int | float):
                raise ValueError(
                    f"field {name!r}: `equals` on a `number` field requires a numeric `value`"
                )
            if ftype == "text" and not isinstance(value, str):
                raise ValueError(
                    f"field {name!r}: `equals` on a `text` field requires a string `value`"
                )
        return self


class SubmissionModel(_StrictModel):
    pass_threshold: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0
    fields: Annotated[list[SubmissionFieldModel], Field(min_length=1)]

    @model_validator(mode="after")
    def unique_field_names(self) -> Self:
        seen: set[str] = set()
        duplicates: list[str] = []
        for f in self.fields:
            if f.name in seen:
                duplicates.append(f.name)
            else:
                seen.add(f.name)
        if duplicates:
            joined = ", ".join(sorted(set(duplicates)))
            raise ValueError(f"duplicate submission field name(s): {joined}")
        return self


class EnvironmentModel(_StrictModel):
    python_version: str
    dependencies: list[str]
    setup_instructions: str


class RawExerciseModel(_StrictModel):
    title: str
    description: str
    sections: Annotated[list[RawSectionModel], Field(min_length=1)]
    expected_outputs: list[RawExpectedOutputModel] = []
    hints: list[str] = []
    submission: SubmissionModel | None = None
    environment: EnvironmentModel | None = None


# ---------------------------------------------------------------------------
# Output (compiled artifact — BR-1 wire shape)
# ---------------------------------------------------------------------------


class CompiledSection(TypedDict):
    title: str
    description: str
    code: str
    editable: bool


class CompiledExpectedImage(TypedDict):
    description: str
    type: Literal["image"]
    path: str
    alt: str


class CompiledExpectedTextOrTable(TypedDict):
    description: str
    type: Literal["text", "table"]
    content: str


CompiledExpectedOutput = CompiledExpectedImage | CompiledExpectedTextOrTable


class CompiledSubmissionField(TypedDict, total=False):
    name: str
    type: Literal["number", "text"]
    label: str
    placeholder: str
    expected: dict[str, Any]


class CompiledSubmission(TypedDict):
    pass_threshold: float
    fields: list[CompiledSubmissionField]


class CompiledEnvironment(TypedDict):
    python_version: str
    dependencies: list[str]
    setup_instructions: str


class CompiledExercise(TypedDict):
    type: Literal["exercise"]
    source: Literal["nbfoundry"]
    ref: str
    status: Literal["ready"]
    title: str
    instructions: str
    sections: list[CompiledSection]
    expected_outputs: list[CompiledExpectedOutput]
    assets: list[str]
    hints: list[str]
    submission: CompiledSubmission | None
    environment: CompiledEnvironment | None
