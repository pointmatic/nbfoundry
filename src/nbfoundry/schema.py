# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Option-C schema (Story I.b).

Two surfaces:

  - **Input** (parsed from YAML): `ExerciseDefinition` + `SectionModel` +
    `EnvironmentModel`. The author-supplied exercise definition.
  - **Output** (assembled by `compile_exercise`, Story I.d): the
    `CompiledExercise` `TypedDict` = `{type, source, ref, title,
    description, hints, environment, notebook_source}`.

The retired static-display models (`Submission*`, `RawExpected*`, the old
`Compiled*` row, the per-section `editable` flag, the top-level
`expected_outputs` field) are intentionally **absent** — Story I.b deletes
them. The no-ML-import contract (FR-7 / AC-10) is preserved: nothing in
this module imports torch, tensorflow, modelfoundry, datarefinery, or the
HuggingFace stack.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal, Self, TypedDict

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ---------------------------------------------------------------------------
# Input models (parsed from YAML)
# ---------------------------------------------------------------------------


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SectionModel(_StrictModel):
    """One section of an exercise definition.

    Exactly one of `code` or `code_file` must be present. The chosen body
    lands inside one marimo code cell at compile time (Story I.c). The
    legacy `editable` flag is gone — cell editability is LearningFoundry's
    `ExerciseBlock` concern.

    `hide_code` (Story I.g) opts the section's code cell into marimo's
    hidden-code state (`@app.cell(hide_code=True)`): the learner sees the
    cell's output but not its source. It does not affect the markdown
    description cell. Default `False` (code visible).
    """

    title: str
    description: str
    code: str | None = None
    code_file: Path | None = None
    hide_code: bool = False

    @model_validator(mode="after")
    def code_xor_code_file(self) -> Self:
        if (self.code is None) == (self.code_file is None):
            raise ValueError("exactly one of `code` or `code_file` is required")
        return self


class EnvironmentModel(_StrictModel):
    """Learner-runtime environment.

    Surfaced verbatim in the compiled output so `learningfoundry launch`
    can install the right deps before spawning marimo. ML frameworks
    declared here are imported only at notebook-run time on the learner's
    machine; the compiler never imports them.
    """

    python_version: str
    dependencies: list[str]
    setup_instructions: str


class ExerciseDefinition(_StrictModel):
    """Author-provided exercise definition (Option C input).

    Replaces the retired `RawExerciseModel`. No `expected_outputs`, no
    `submission` — those static-display fields are gone with BR-4/BR-5.
    """

    title: str
    description: str
    sections: Annotated[list[SectionModel], Field(min_length=1)]
    hints: list[str] = []
    environment: EnvironmentModel | None = None


# ---------------------------------------------------------------------------
# Output (compiled artifact — Option C wire shape)
# ---------------------------------------------------------------------------


class CompiledEnvironment(TypedDict):
    python_version: str
    dependencies: list[str]
    setup_instructions: str


class CompiledExercise(TypedDict):
    """Option-C wire shape returned by `compile_exercise` (Story I.d).

    `description` and `hints` are HTML (banner markdown is rendered by the
    compiler). `notebook_source` is a complete, self-contained
    `marimo.App()` module **as a string** — the `.py` notebook the learner
    runs locally via `marimo edit|run`.
    """

    type: Literal["exercise"]
    source: Literal["nbfoundry"]
    ref: str
    title: str
    description: str
    hints: list[str]
    environment: CompiledEnvironment | None
    notebook_source: str
